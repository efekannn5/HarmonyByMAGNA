"""
Database Monitoring Service
Sürekli veri tabanı tablolarını izler ve yeni kayıtları tespit eder
"""

import time
import threading
from datetime import datetime, timedelta, date
from typing import Dict, List, Callable
from sqlalchemy import text
from flask import current_app
from ..extensions import db
from ..models.dolly import DollyEOLInfo
from .audit_service import AuditService

class DatabaseMonitor:
    def __init__(self):
        self.is_running = False
        self.monitoring_thread = None
        self.last_check_times = {}
        self.last_processed_ids = {'DollyEOLInfo': set()}
        self.callbacks = {
            'new_dolly': [],
            'dolly_updated': [],
            'dolly_status_changed': []
        }
        self.check_interval = 2  # Her 2 saniyede kontrol et (performans için optimize edildi)
        self.app = None  # Flask app referansı
        self.audit = AuditService()
        # Cache management
        self.max_processed_ids = 1000  # Maksimum cache boyutu (bellekten tasarruf)
        self.cache_cleanup_counter = 0
        self.cache_cleanup_interval = 300  # Her 300 sorgudan bir (10 dakika) cache temizle
        
    def start_monitoring(self, app=None):
        """Monitoring'i başlat"""
        if self.is_running:
            if app:
                app.logger.warning("Database monitoring already running")
            return
            
        if app:
            self.app = app
            
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
        if self.app:
            self.app.logger.info("🔄 Database monitoring started")
        else:
            print("🔄 Database monitoring started")
        
    def stop_monitoring(self):
        """Monitoring'i durdur"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        try:
            current_app.logger.info("⏹️ Database monitoring stopped")
        except RuntimeError:
            # Application context yoksa print kullan
            print("⏹️ Database monitoring stopped")
        
    def register_callback(self, event_type: str, callback: Callable):
        """Event callback'i kaydet"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            
    def _monitor_loop(self):
        """Ana monitoring döngüsü"""
        if self.app:
            self.app.logger.info("🚀 Database monitoring loop started")
        else:
            print("🚀 Database monitoring loop started")
        
        while self.is_running:
            try:
                if self.app:
                    with self.app.app_context():
                        # DollyEOLInfo tablosunu kontrol et
                        self._check_dolly_eol_info()
                        
                        # SQLAlchemy session temizliği - bellek sızıntısını önle
                        db.session.remove()
                        
                        # Diğer kritik tabloları da kontrol edebiliriz
                        # self._check_dolly_submissions()
                        # self._check_web_operator_tasks()
                else:
                    # App context olmadan çalışma durumu
                    print("⚠️ No app context available for monitoring")
                    
                time.sleep(self.check_interval)
                
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"Database monitoring error: {e}")
                else:
                    print(f"Database monitoring error: {e}")
                time.sleep(5)  # Hata durumunda biraz bekle
                
    def _check_dolly_eol_info(self):
        """DollyEOLInfo tablosundaki yeni kayıtları kontrol et"""
        try:
            table_name = 'DollyEOLInfo'
            last_check = self.last_check_times.get(table_name)
            
            # Periyodik cache temizliği - bellek optimizasyonu
            self.cache_cleanup_counter += 1
            if self.cache_cleanup_counter >= self.cache_cleanup_interval:
                self._cleanup_cache()
                self.cache_cleanup_counter = 0
            
            if last_check is None:
                # İlk çalıştırma - son 1 dakikayı kontrol et
                last_check = datetime.now() - timedelta(minutes=1)
                self.last_check_times[table_name] = last_check
                
            # Yeni kayıtları bul
            new_records = self._get_new_dolly_records(last_check)
            processed_set = self.last_processed_ids.setdefault(table_name, set())
            seen_in_cycle: set = set()
            unique_records = []

            for record in new_records:
                dolly_no = record.get('DollyNo')
                if dolly_no in processed_set or dolly_no in seen_in_cycle:
                    continue
                seen_in_cycle.add(dolly_no)
                unique_records.append(record)
                processed_set.add(dolly_no)
                
                # Bellek yönetimi - cache boyutu sınırlama
                if len(processed_set) > self.max_processed_ids:
                    # En eski %20'yi temizle (FIFO yaklaşımı)
                    to_remove = list(processed_set)[:int(self.max_processed_ids * 0.2)]
                    processed_set.difference_update(to_remove)
            
            if unique_records:
                current_app.logger.info(f"🆕 {len(unique_records)} new dolly record(s) found")
                
                for record in unique_records:
                    dolly_no = record.get('DollyNo')

                    # Callback'leri çağır
                    self._trigger_callbacks('new_dolly', record)
                    
                    # Audit log'a kaydet
                    self.audit.log(
                        action='NEW_DOLLY_DETECTED',
                        resource='DollyEOLInfo',
                        resource_id=str(dolly_no or ''),
                        actor_name='system',
                        metadata={
                            'details': f"New dolly detected: {dolly_no or 'Unknown'}"
                        }
                    )
                    
            # Son kontrol zamanını güncelle
            self.last_check_times[table_name] = datetime.now()
            
        except Exception as e:
            current_app.logger.error(f"Error checking DollyEOLInfo: {e}")
            
    def _get_new_dolly_records(self, since_datetime: datetime) -> List[Dict]:
        """Belirli bir tarihten sonraki yeni dolly kayıtlarını getir"""
        try:
            # DollyEOLInfo tablosundaki gerçek sütun isimleri kullan - Performans için optimize edildi
            query = text("""
                SELECT TOP 20
                    DollyNo,
                    VinNo,
                    CustomerReferans,
                    Adet,
                    EOLName,
                    EOLID,
                    EOLDATE,
                    EOLDollyBarcode
                FROM DollyEOLInfo WITH (NOLOCK)
                WHERE EOLDATE >= :since_dt
                ORDER BY EOLDATE DESC
            """)
            
            result = db.session.execute(query, {'since_dt': since_datetime})
            records = [dict(row._mapping) for row in result]
            
            # Yeni kayıtları filtrele (son kontrol zamanından sonraki)
            new_records = []
            for record in records:
                record_time = record.get('EOLDATE')
                if record_time:
                    if isinstance(record_time, datetime) and record_time >= since_datetime:
                        new_records.append(record)
                    elif isinstance(record_time, date) and record_time >= since_datetime.date():
                        new_records.append(record)
                        
            return new_records
            
        except Exception as e:
            if self.app:
                self.app.logger.error(f"Error fetching new dolly records: {e}")
            else:
                print(f"Error fetching new dolly records: {e}")
            return []
            
    def _trigger_callbacks(self, event_type: str, data: Dict):
        """Event callback'lerini tetikle"""
        try:
            for callback in self.callbacks.get(event_type, []):
                try:
                    callback(data)
                except Exception as e:
                    current_app.logger.error(f"Callback error for {event_type}: {e}")
        except Exception as e:
            current_app.logger.error(f"Error triggering callbacks: {e}")
    
    def _cleanup_cache(self):
        """Cache temizliği - bellek optimizasyonu"""
        try:
            for table_name, processed_set in self.last_processed_ids.items():
                original_size = len(processed_set)
                if original_size > self.max_processed_ids:
                    # Sadece son max_processed_ids/2 kadarını tut
                    items_to_keep = list(processed_set)[-(self.max_processed_ids // 2):]
                    processed_set.clear()
                    processed_set.update(items_to_keep)
                    
                    if self.app:
                        self.app.logger.info(
                            f"🧹 Cache cleaned for {table_name}: {original_size} -> {len(processed_set)} items"
                        )
                    else:
                        print(f"🧹 Cache cleaned for {table_name}: {original_size} -> {len(processed_set)} items")
        except Exception as e:
            if self.app:
                self.app.logger.error(f"Cache cleanup error: {e}")
            else:
                print(f"Cache cleanup error: {e}")
            
    def get_monitoring_stats(self) -> Dict:
        """Monitoring istatistiklerini getir"""
        return {
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'last_check_times': {
                table: check_time.isoformat() if check_time else None
                for table, check_time in self.last_check_times.items()
            },
            'registered_callbacks': {
                event: len(callbacks)
                for event, callbacks in self.callbacks.items()
            }
        }

# Global instance
db_monitor = DatabaseMonitor()

# Notification handlers
def on_new_dolly(dolly_data: Dict):
    """Yeni dolly geldiğinde çalışan handler"""
    from flask import current_app
    try:
        if current_app:
            current_app.logger.info(f"🚛 New dolly notification: {dolly_data.get('DollyNo')}")
        else:
            print(f"🚛 New dolly notification: {dolly_data.get('DollyNo')}")
        
        # Burada istediğimiz aksiyonları alabiliriz:
        # - Email notification
        # - WebSocket notification  
        # - Slack notification
        # - Database trigger
        
        # Örnek: EOL Name kontrolü
        eol_name = dolly_data.get('EOLName', '')
        if 'URGENT' in eol_name.upper() or 'CRITICAL' in eol_name.upper():
            if current_app:
                current_app.logger.warning(f"⚠️ Urgent dolly detected: {dolly_data.get('DollyNo')}")
            else:
                print(f"⚠️ Urgent dolly detected: {dolly_data.get('DollyNo')}")
    except:
        pass  # Context dışında çalışabilir

def on_dolly_updated(dolly_data: Dict):
    """Dolly güncellendiğinde çalışan handler"""
    from flask import current_app
    try:
        if current_app:
            current_app.logger.info(f"📝 Dolly updated: {dolly_data.get('DollyNo')}")
        else:
            print(f"📝 Dolly updated: {dolly_data.get('DollyNo')}")
    except:
        pass

# Register default callbacks
db_monitor.register_callback('new_dolly', on_new_dolly)
db_monitor.register_callback('dolly_updated', on_dolly_updated)
