@echo off
setlocal
cd /d "%~dp0"
title SPECIMEN.SYS / Build Windows executable
if not exist ".venv\Scripts\python.exe" (
  echo Run INSTALL.cmd first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install "pyinstaller>=6.10,<7"
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name SPECIMEN.SYS --icon "branding\specimen.ico" --add-data "specimen_sys\assets;specimen_sys\assets" --add-data "branding;branding" --hidden-import specimen_sys.app specimen.pyw
if errorlevel 1 goto :failed
echo EXE created in dist\SPECIMEN.SYS\
pause
exit /b 0
:failed
echo Build failed. Review the output above.
pause
exit /b 1
