@echo off
setlocal
cd /d "%~dp0"
title SPECIMEN.SYS / INSTALL
where py >nul 2>&1
if errorlevel 1 (
  echo Python Launcher not found. Install Python 3.11+ from python.org.
  echo This script will not alter Windows settings.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed
echo.
echo Installation complete. Run RUN-SPECIMEN.cmd.
pause
exit /b 0
:failed
echo.
echo Installation failed. No Windows startup or security settings were changed.
pause
exit /b 1
