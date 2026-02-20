@echo off
REM ==== AYARLANACAK KISIMLAR ====
set NSSM_EXE=C:\Tools\nssm\nssm.exe
set PYTHON_EXE=C:\Users\svc_intercompany_inv\AppData\Local\Programs\Python\Python313\python.exe
set SERVICE_NAME=HarmonyAsılDollyEOLService
set DISPLAY_NAME=Harmony asıl bu Dolly EOL JSON Service
set SERVICE_DIR=C:\Users\svc_intercompany_inv\Documents\DollyEOLService
set SCRIPT_PATH=%SERVICE_DIR%\dolly_service.py

REM ==== SERVIS OLUŞTUR ====
echo Installing service %SERVICE_NAME% ...

"%NSSM_EXE%" install %SERVICE_NAME% "%PYTHON_EXE%" "%SCRIPT_PATH%"

REM Çalışma dizinini ayarla (loglar, config vs. doğru yerden açılsın)
"%NSSM_EXE%" set %SERVICE_NAME% AppDirectory "%SERVICE_DIR%"

REM Görünen adı ve açıklamayı ayarla
"%NSSM_EXE%" set %SERVICE_NAME% DisplayName "%DISPLAY_NAME%"
"%NSSM_EXE%" set %SERVICE_NAME% Description "Receives Dolly EOL JSON posts and writes them into SQL Server."

REM Servis başlarken otomatik kalksın
"%NSSM_EXE%" set %SERVICE_NAME% Start SERVICE_AUTO_START

echo Service %SERVICE_NAME% installed.
echo To start the service, run:  sc start %SERVICE_NAME%
pause
