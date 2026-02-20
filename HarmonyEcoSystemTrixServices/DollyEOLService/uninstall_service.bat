@echo off
set NSSM_EXE=C:\Tools\nssm\nssm.exe
set SERVICE_NAME=HarmonyDollyEOLService

echo Stopping service %SERVICE_NAME% ...
sc stop %SERVICE_NAME% >NUL 2>&1

echo Removing service %SERVICE_NAME% ...
"%NSSM_EXE%" remove %SERVICE_NAME% confirm

echo Service %SERVICE_NAME% removed.
pause
