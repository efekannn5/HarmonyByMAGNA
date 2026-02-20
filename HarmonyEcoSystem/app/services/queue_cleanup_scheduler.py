"""
Queue Cleanup Scheduler
Arşivlenmiş dolly'lerin otomatik temizlenmesi için zamanlayıcı
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from flask import Flask


class QueueCleanupScheduler:
    """Periyodik olarak süresi dolmuş arşiv kayıtlarını temizler"""
    
    def __init__(self):
        self.app: Optional[Flask] = None
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.cleanup_interval_minutes = 60  # Her 60 dakikada bir kontrol et
        
    def start_scheduler(self, app: Flask):
        """Scheduler'ı başlat"""
        if self.is_running:
            app.logger.warning("⚠️ Queue cleanup scheduler zaten çalışıyor")
            return
        
        self.app = app
        self.is_running = True
        self._stop_event.clear()
        
        self._thread = threading.Thread(
            target=self._cleanup_loop,
            name="QueueCleanupThread",
            daemon=True
        )
        self._thread.start()
        
        app.logger.info(
            f"✅ Queue cleanup scheduler başlatıldı "
            f"(interval: {self.cleanup_interval_minutes} dakika)"
        )
    
    def stop_scheduler(self):
        """Scheduler'ı durdur"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        if self.app:
            self.app.logger.info("🛑 Queue cleanup scheduler durduruldu")
    
    def _cleanup_loop(self):
        """Ana cleanup döngüsü"""
        while self.is_running and not self._stop_event.is_set():
            try:
                # Cleanup işlemini çalıştır
                self._run_cleanup()
                
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"❌ Queue cleanup error: {e}", exc_info=True)
            
            # Sonraki çalışmaya kadar bekle
            self._stop_event.wait(timeout=self.cleanup_interval_minutes * 60)
    
    def _run_cleanup(self):
        """Cleanup işlemini çalıştır"""
        if not self.app:
            return
        
        with self.app.app_context():
            try:
                from app.services import DollyService
                
                service = DollyService(self.app.config.get("APP_CONFIG", {}))
                result = service.cleanup_expired_removed_dollys()
                
                if result['deleted_count'] > 0:
                    self.app.logger.info(
                        f"🧹 Otomatik temizlik: {result['deleted_count']} "
                        f"süre dolmuş kayıt silindi"
                    )
                
            except Exception as e:
                self.app.logger.error(f"❌ Cleanup service error: {e}", exc_info=True)
    
    def trigger_manual_cleanup(self):
        """Manuel cleanup tetikle (API endpoint için)"""
        if not self.app:
            raise RuntimeError("Scheduler başlatılmamış")
        
        with self.app.app_context():
            from app.services import DollyService
            
            service = DollyService(self.app.config.get("APP_CONFIG", {}))
            return service.cleanup_expired_removed_dollys()


# Global scheduler instance
queue_cleanup_scheduler = QueueCleanupScheduler()
