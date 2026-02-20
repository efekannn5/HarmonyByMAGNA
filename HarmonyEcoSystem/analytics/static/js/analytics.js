/**
 * HarmonyEcoSystem Analytics Platform - Core JavaScript
 * ========================================================
 * Common utilities and helpers for analytics dashboard
 */

// Global Analytics Object
const Analytics = {
    config: {
        refreshInterval: 30000, // 30 seconds
        apiBaseUrl: '/analytics/api'
    },
    
    /**
     * Make API request with error handling
     */
    async fetchData(endpoint, params = {}) {
        try {
            const url = new URL(this.config.apiBaseUrl + endpoint, window.location.origin);
            Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            this.showError('Failed to fetch data: ' + error.message);
            throw error;
        }
    },
    
    /**
     * Format number with locale
     */
    formatNumber(num, decimals = 0) {
        if (num === null || num === undefined) return '-';
        return Number(num).toLocaleString('tr-TR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },
    
    /**
     * Format duration in hours
     */
    formatHours(hours) {
        if (hours === null || hours === undefined) return '-';
        
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        
        if (h === 0) {
            return m + ' min';
        } else if (m === 0) {
            return h + ' hr';
        } else {
            return h + ' hr ' + m + ' min';
        }
    },
    
    /**
     * Format percentage
     */
    formatPercent(value, decimals = 1) {
        if (value === null || value === undefined) return '-';
        return Number(value).toFixed(decimals) + '%';
    },
    
    /**
     * Get status badge HTML
     */
    getStatusBadge(status) {
        const statusMap = {
            'PRODUCTION': { class: 'primary', text: 'Production' },
            'SCANNING': { class: 'info', text: 'Scanning' },
            'LOADING_COMPLETED': { class: 'warning', text: 'Loading' },
            'WEB_PROCESSING': { class: 'secondary', text: 'Processing' },
            'COMPLETED': { class: 'success', text: 'Completed' }
        };
        
        const config = statusMap[status] || { class: 'secondary', text: status };
        return `<span class="badge bg-${config.class}">${config.text}</span>`;
    },
    
    /**
     * Get alert level badge HTML
     */
    getAlertBadge(level) {
        const levelMap = {
            'CRITICAL': { class: 'danger', icon: 'exclamation-triangle-fill' },
            'WARNING': { class: 'warning', icon: 'exclamation-triangle' },
            'ATTENTION': { class: 'info', icon: 'info-circle' },
            'NORMAL': { class: 'success', icon: 'check-circle' }
        };
        
        const config = levelMap[level] || { class: 'secondary', icon: 'question-circle' };
        return `<span class="badge bg-${config.class}">
            <i class="bi bi-${config.icon}"></i> ${level}
        </span>`;
    },
    
    /**
     * Show error message
     */
    showError(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-triangle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('main');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
        }
    },
    
    /**
     * Show success message
     */
    showSuccess(message) {
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="bi bi-check-circle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('main');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
        }
    },
    
    /**
     * Export table to CSV
     */
    exportToCSV(tableId, filename = 'export.csv') {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        for (const row of rows) {
            const cols = row.querySelectorAll('td, th');
            const csvRow = [];
            
            for (const col of cols) {
                csvRow.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
            }
            
            csv.push(csvRow.join(','));
        }
        
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    },
    
    /**
     * Get date range (helper)
     */
    getDateRange(days = 7) {
        const today = new Date();
        const from = new Date(today);
        from.setDate(from.getDate() - days);
        
        return {
            from: from.toISOString().split('T')[0],
            to: today.toISOString().split('T')[0]
        };
    },
    
    /**
     * Initialize date pickers
     */
    initDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        const today = new Date().toISOString().split('T')[0];
        
        dateInputs.forEach(input => {
            if (!input.value) {
                if (input.name === 'date_from') {
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    input.value = weekAgo.toISOString().split('T')[0];
                } else if (input.name === 'date_to') {
                    input.value = today;
                }
            }
        });
    }
};

// Chart Utilities
const ChartUtils = {
    /**
     * Common chart options
     */
    commonOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    },
    
    /**
     * Color palette
     */
    colors: {
        primary: 'rgb(13, 110, 253)',
        success: 'rgb(25, 135, 84)',
        danger: 'rgb(220, 53, 69)',
        warning: 'rgb(255, 193, 7)',
        info: 'rgb(13, 202, 240)',
        secondary: 'rgb(108, 117, 125)'
    },
    
    /**
     * Get color with alpha
     */
    getColor(name, alpha = 1) {
        const color = this.colors[name] || this.colors.primary;
        return color.replace('rgb', 'rgba').replace(')', `, ${alpha})`);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers
    Analytics.initDatePickers();
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Make Analytics globally available
window.Analytics = Analytics;
window.ChartUtils = ChartUtils;
