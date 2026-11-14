@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please run INSTALL.cmd first.
  pause
  exit /b 1
)
echo PRIVATE DIAGNOSTIC SESSION
 echo Local diagnostic logs may contain file paths, computer details and error information.
echo Do not attach the raw logs or full desktop screenshots to public GitHub issues.
set "SPECIMEN_DEBUG_LOGS=1"
".venv\Scripts\python.exe" specimen.py
set "rc=%errorlevel%"
echo.
echo SPECIMEN.SYS exited with code %rc%.
echo Diagnostic logs, if written, are in your own local application-data folder.
echo Review and redact them before sharing.
pause
exit /b %rc%
