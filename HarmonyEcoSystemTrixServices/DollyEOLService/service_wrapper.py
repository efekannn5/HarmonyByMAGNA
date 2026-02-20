import os
import sys
import subprocess

import win32serviceutil
import win32service
import win32event
import servicemanager


class DollyEOLWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Harmony DollyEOLJsonService"
    _svc_display_name_ = "Dolly EOL JSON Listener Service"
    _svc_description_ = "Receives EOL JSON posts and writes them into SQL Server (DollyEOLInfo)."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogInfoMsg("DollyEOLJsonService stopping...")
        if self.process is not None:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("DollyEOLJsonService starting...")
        python_exe = sys.executable
        script_path = os.path.join(os.path.dirname(__file__), "dolly_service.py")

        # Flask servis scriptini alt proses olarak başlat
        self.process = subprocess.Popen([python_exe, script_path])

        # Servis durdurulana kadar bekle
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        servicemanager.LogInfoMsg("DollyEOLJsonService stopped.")


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DollyEOLWinService)
