@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
 .venv\Scripts\python.exe launch.py
) else (
 echo Run Setup.cmd once, then double-click Start Project.cmd again.
)
pause
