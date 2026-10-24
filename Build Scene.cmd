@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Run Setup.cmd first.
 pause
 exit /b 1
)
echo In CoppeliaSim, save your work and open File ^> New scene before continuing.
pause
.venv\Scripts\python.exe run.py --build
pause
