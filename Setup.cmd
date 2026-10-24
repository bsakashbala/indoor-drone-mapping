@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Setup complete. Open IndoorDroneMapping.ttt, then use Run Mapping.cmd.
pause
exit /b 0
:fail
echo Setup failed. Check that Python 3.10 or newer and internet access are available.
pause
exit /b 1
