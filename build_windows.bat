@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or newer from python.org.
  pause
  exit /b 1
)
py -m pip install --upgrade pip
if errorlevel 1 goto :failed
py -m pip install -r requirements.txt
if errorlevel 1 goto :failed
py -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name "Epson EcoTank ID Converter" ^
  --add-data "template_base;template_base" ^
  --collect-all pymupdf ^
  main.py
if errorlevel 1 goto :failed
echo.
echo App bundle complete: dist\Epson EcoTank ID Converter\
echo To make Setup.exe, install Inno Setup and compile installer.iss.
pause
exit /b 0
:failed
echo.
echo Build failed. Review the messages above.
pause
exit /b 1
