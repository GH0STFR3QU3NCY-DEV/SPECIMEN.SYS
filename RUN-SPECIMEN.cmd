@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo SPECIMEN.SYS is not installed. Please run INSTALL.cmd first.
  pause
  exit /b 1
)
start "SPECIMEN.SYS" ".venv\Scripts\pythonw.exe" specimen.pyw
