function ensureNotificationPermission() {
  if (!window.Notification) return;
  if (Notification.permission === 'default') {
    Notification.requestPermission().catch(() => {});
  }
}

function maybeSystemNotify(message, type = 'info') {
  if (!window.Notification) return;
  if (Notification.permission !== 'granted') return;
  // Sadece sekme arka plandayken sistem bildirimi göster
  if (!document.hidden) return;
  const icon = '/static/img/logo.png';
  try {
    new Notification('Harmony', {
      body: message,
      icon: icon,
      badge: icon,
      tag: `harmony-${type}-${Date.now()}`
    });
  } catch (e) {
    console.warn('System notification failed:', e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Bildirim izni iste (tek sefer)
  ensureNotificationPermission();

  const nav = document.getElementById("primaryNav");
  const toggle = document.getElementById("navToggle");

  if (!nav || !toggle) {
    return;
  }

  const closeNav = () => {
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  };

  const openNav = () => {
    nav.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
  };

  toggle.addEventListener("click", () => {
    if (nav.classList.contains("is-open")) {
      closeNav();
    } else {
      openNav();
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 1024) {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });

  // ============================================
  // Real-time Updates via Socket.IO
  // ============================================
  
  // Initialize Socket.IO connection - Optimized settings
  const socket = io({
    reconnection: true,
    reconnectionDelay: 2000,        // İlk yeniden bağlanma 2 saniye sonra
    reconnectionDelayMax: 10000,    // Maksimum 10 saniye bekle
    reconnectionAttempts: Infinity, // Sınırsız deneme
    timeout: 20000,                 // Bağlantı timeout 20 saniye
    transports: ['websocket', 'polling']  // Önce websocket, sonra polling
  });

  // Connection state tracking
  let isConnected = false;
  let connectionLostShown = false;
  let reconnectNotificationTimeout = null;

  // Connection status handlers
  socket.on('connect', () => {
    console.log('✅ Real-time updates connected');
    isConnected = true;
    
    // Sadece yeniden bağlanma sonrası bildirim göster
    if (connectionLostShown) {
      showNotification('Canlı güncellemeler yeniden bağlandı', 'success', 2000);
      connectionLostShown = false;
    }
    
    // Reconnect notification timeout'u temizle
    if (reconnectNotificationTimeout) {
      clearTimeout(reconnectNotificationTimeout);
      reconnectNotificationTimeout = null;
    }
  });

  socket.on('disconnect', (reason) => {
    console.log('❌ Real-time updates disconnected:', reason);
    isConnected = false;
    
    // Sadece sunucu kaynaklı veya beklenmeyen kopmalarda bildir
    // 'io server disconnect' = sunucu kapatma
    // 'transport close' = ağ sorunu
    if (reason === 'io server disconnect' || reason === 'transport close') {
      // 5 saniye sonra hala bağlı değilse bildirim göster
      reconnectNotificationTimeout = setTimeout(() => {
        if (!isConnected) {
          showNotification('Bağlantı sorunu - yeniden bağlanılıyor...', 'warning', 3000);
          connectionLostShown = true;
        }
      }, 5000);
    }
  });

  socket.on('reconnect', (attemptNumber) => {
    console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
    // Bildirim connect event'inde gösteriliyor
  });
  
  socket.on('reconnect_error', (error) => {
    console.error('🔴 Reconnection error:', error);
  });
  
  socket.on('reconnect_failed', () => {
    console.error('🔴 Reconnection failed completely');
    showNotification('Sunucuya bağlanılamıyor. Lütfen sayfayı yenileyin.', 'error', 10000);
  });

  // Listen for dolly updates
  socket.on('dolly_update', (payload) => {
    console.log('📦 Dolly update received:', payload);
    
    const { type, data } = payload;
    
    // Show notification based on event type
    switch(type) {
      case 'manual_collection':
        showNotification(
          `Manuel toplama: ${data.group_name} - ${data.dolly_count} dolly (${data.actor})`, 
          'info', 
          5000
        );
        reloadCurrentPageData();
        break;
        
      case 'manual_submit_completed':
        showNotification(
          `✅ ${data.dolly_count || 0} dolly / ${data.vin_count || 0} VIN submit edildi • ${data.part_number || ''}`,
          'success',
          5000
        );
        reloadCurrentPageData();
        break;
        
      case 'group_created':
        showNotification(`Yeni grup oluşturuldu: ${data.group_name}`, 'success', 4000);
        reloadCurrentPageData();
        break;
        
      case 'shipment_updated':
        showNotification(`Sevkiyat güncellendi: ${data.shipment_tag} - ${data.status}`, 'info', 4000);
        reloadCurrentPageData();
        break;
        
      case 'task_updated':
        showNotification(`Görev güncellendi`, 'info', 3000);
        reloadCurrentPageData();
        break;
        
      case 'new_dollys_available':
        showNotification(
          `✨ ${data.new_count} yeni dolly eklendi! Kartlar otomatik açılıyor...`, 
          'success', 
          5000
        );
        reloadCurrentPageData();
        break;
        
      default:
        // Generic update - reload data
        reloadCurrentPageData();
    }
  });

  // Listen for task updates
  socket.on('task_update', (payload) => {
    console.log('📋 Task update received:', payload);
    showNotification(`Görev #${payload.task_id} durumu: ${payload.status}`, 'info', 3000);
    reloadCurrentPageData();
  });

  // Listen for notifications
  socket.on('notification', (payload) => {
    showNotification(payload.message, payload.notification_type || 'info', 5000);
  });

  // ============================================
  // Helper Functions
  // ============================================
  
  /**
   * Show toast notification
   */
  function showNotification(message, type = 'info', duration = 3000) {
    // Sistem bildirimi de tetikle (arka plandaysa)
    maybeSystemNotify(message, type);

    // Remove existing notifications
    const existing = document.querySelector('.realtime-notification');
    if (existing) existing.remove();
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `realtime-notification realtime-notification--${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto remove
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, duration);
  }

  /**
   * Reload current page data without full page refresh
   */
  function reloadCurrentPageData() {
    const currentPath = window.location.pathname;
    
    // For dashboard pages, reload specific sections
    if (currentPath === '/' || currentPath.includes('/dashboard')) {
      reloadDashboardSections();
    } else if (currentPath.includes('/manual-collection')) {
      reloadManualCollectionData();
    } else if (currentPath.includes('/groups/manage')) {
      reloadGroupsData();
    } else if (currentPath.includes('/operator')) {
      reloadOperatorData();
    }
  }

  /**
   * Reload dashboard sections via AJAX
   */
  function reloadDashboardSections() {
    // Reload the page content areas that show dynamic data
    const tables = document.querySelectorAll('table tbody');
    if (tables.length === 0) return;
    
    // Add a subtle loading indicator
    tables.forEach(table => {
      if (!table.classList.contains('reloading')) {
        table.classList.add('reloading');
      }
    });
    
    // Reload page after a short delay to batch updates
    clearTimeout(window.reloadTimer);
    window.reloadTimer = setTimeout(() => {
      fetch(window.location.href, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(response => response.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Update table bodies
        const newTables = doc.querySelectorAll('table tbody');
        newTables.forEach((newTable, index) => {
          if (tables[index]) {
            tables[index].innerHTML = newTable.innerHTML;
            tables[index].classList.remove('reloading');
          }
        });
        
        // Update any count badges
        const countBadges = document.querySelectorAll('.count-badge, .badge');
        const newCountBadges = doc.querySelectorAll('.count-badge, .badge');
        newCountBadges.forEach((newBadge, index) => {
          if (countBadges[index]) {
            countBadges[index].textContent = newBadge.textContent;
          }
        });
      })
      .catch(err => {
        console.error('Failed to reload data:', err);
        tables.forEach(table => table.classList.remove('reloading'));
      });
    }, 500);
  }

  /**
   * Reload manual collection data - smart update without page refresh
   */
  function reloadManualCollectionData() {
    const dollysGrid = document.getElementById('dollysGrid');
    if (!dollysGrid) return;
    
    console.log('🔄 Manuel toplama verileri güncelleniyor...');
    
    // Store current state
    const currentDollyNos = new Set();
    const currentlyOpenCards = new Set();
    const selectedDollys = new Set();
    
    // Remember which cards are open and selected
    document.querySelectorAll('.dolly-card').forEach(card => {
      const dollyNo = card.dataset.dollyNo;
      currentDollyNos.add(dollyNo);
      
      if (card.classList.contains('expanded')) {
        currentlyOpenCards.add(dollyNo);
      }
      if (card.classList.contains('selected')) {
        selectedDollys.add(dollyNo);
      }
    });
    
    // Fetch updated data
    fetch(window.location.href)
      .then(response => response.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newGrid = doc.getElementById('dollysGrid');
        
        if (!newGrid) return;
        
        // Find new dollys
        const newDollyNos = new Set();
        const newDollyCards = [];
        
        newGrid.querySelectorAll('.dolly-card').forEach(card => {
          const dollyNo = card.dataset.dollyNo;
          newDollyNos.add(dollyNo);
          
          if (!currentDollyNos.has(dollyNo)) {
            newDollyCards.push({
              dollyNo: dollyNo,
              element: card,
              vinCount: card.dataset.vinCount
            });
          }
        });
        
        // Update the grid
        dollysGrid.innerHTML = newGrid.innerHTML;
        
        // Re-initialize the page after update
        if (typeof initManualCollection === 'function') {
          initManualCollection();
        }
        
        // Restore selected state
        setTimeout(() => {
          document.querySelectorAll('.dolly-card').forEach(card => {
            const dollyNo = card.dataset.dollyNo;
            
            // Restore selection
            if (selectedDollys.has(dollyNo)) {
              card.classList.add('selected');
            }
            
            // Restore expanded state or auto-expand new cards
            if (currentlyOpenCards.has(dollyNo) || !currentDollyNos.has(dollyNo)) {
              card.classList.add('expanded');
              
              // Auto-scroll to new card and highlight it
              if (!currentDollyNos.has(dollyNo)) {
                setTimeout(() => {
                  card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  card.style.animation = 'newCardHighlight 2s ease-out';
                }, 300);
              }
            }
          });
          
          // Update counts
          updateCounts();
        }, 100);
        
        // Show notification for new dollys
        if (newDollyCards.length > 0) {
          const totalVins = newDollyCards.reduce((sum, d) => sum + parseInt(d.vinCount || 0), 0);
          console.log(`✨ ${newDollyCards.length} yeni dolly eklendi (${totalVins} VIN)`);
          showNotification(
            `${newDollyCards.length} yeni dolly eklendi (${totalVins} VIN) - Kartlar otomatik açıldı`,
            'success',
            5000
          );
        }
      })
      .catch(err => console.error('Failed to reload manual collection:', err));
  }

  /**
   * Reload groups management data
   */
  function reloadGroupsData() {
    const groupsList = document.querySelector('.groups-list');
    if (!groupsList) return;
    
    fetch(window.location.href)
      .then(response => response.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newGroupsList = doc.querySelector('.groups-list');
        if (newGroupsList) {
          groupsList.innerHTML = newGroupsList.innerHTML;
        }
      })
      .catch(err => console.error('Failed to reload groups:', err));
  }

  /**
   * Reload operator dashboard data
   */
  function reloadOperatorData() {
    const taskLists = document.querySelectorAll('.task-list');
    if (taskLists.length === 0) return;
    
    fetch(window.location.href)
      .then(response => response.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newTaskLists = doc.querySelectorAll('.task-list');
        
        newTaskLists.forEach((newList, index) => {
          if (taskLists[index]) {
            taskLists[index].innerHTML = newList.innerHTML;
          }
        });
      })
      .catch(err => console.error('Failed to reload operator data:', err));
  }

  // Make socket available globally for debugging
  window.harmonySocket = socket;
});
