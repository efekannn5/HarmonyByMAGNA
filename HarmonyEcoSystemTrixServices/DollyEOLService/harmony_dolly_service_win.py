#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harmony Dolly EOL - Windows Service
Flask uygulamasını Windows Service olarak çalıştırır
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import threading

class HarmonyDollyEOLService(win32serviceutil.ServiceFramework):
    # Windows iç servis adı (boşluk yok)
    _svc_name_ = "HarmonyDollyEOLService"
    # Services.msc ekranında görünen ad
    _svc_display_name_ = "Harmony Dolly EOL JSON Service"
    # Services.msc açıklama
    _svc_description_ = (
        "Dolly EOL JSON verilerini alıp SQL Server üzerindeki DollyEOLInfo tablosuna yazan web servisi."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        """Service durdurulduğunda çağrılır"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )
        self.is_alive = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        """Service başlatıldığında çağrılır"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, 'Service başlatıldı')
        )

        try:
            self.main()
        except Exception as e:
            servicemanager.LogErrorMsg(f"Harmony Dolly EOL service hatası: {str(e)}")

    def main(self):
        """Ana Flask uygulamasını çalıştırır"""
        try:
            # Çalışma dizinini ayarla
            service_dir = os.path.dirname(__file__)
            if not service_dir:
                # Fallback – senin DollyEOLService klasörün
                service_dir = r"C:\Users\svc_ymcharmony\Documents\HarmonyEcoSystemTrixServices\DollyEOLService"

            os.chdir(service_dir)

            # Flask uygulamasını import edebilmek için path'e ekle
            sys.path.insert(0, service_dir)

            # Flask uygulamasını thread olarak çalıştır
            flask_thread = threading.Thread(target=self.run_flask_app)
            flask_thread.daemon = True
            flask_thread.start()

            # Service durdurulana kadar bekle
            while self.is_alive:
                if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                    break

        except Exception as e:
            servicemanager.LogErrorMsg(f"Harmony Dolly EOL main hatası: {str(e)}")

    def run_flask_app(self):
        """Flask uygulamasını çalıştırır"""
        try:
            # DİKKAT: dolly_service.py içinde 'app = Flask(__name__)' olmalı
            from dolly_service import app

            # Production ayarları
            app.run(
                debug=False,
                host='0.0.0.0',
                port=8181,
                threaded=True,
                use_reloader=False
            )
        except Exception as e:
            servicemanager.LogErrorMsg(f"Harmony Dolly EOL Flask hatası: {str(e)}")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Service olarak çalıştırılıyor
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(HarmonyDollyEOLService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Komut satırı (install/start/stop/remove vs.)
        win32serviceutil.HandleCommandLine(HarmonyDollyEOLService)
