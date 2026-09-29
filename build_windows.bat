@echo off
setlocal
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean Smart_Repair_Controller_Test6.spec
if errorlevel 1 (
  echo BUILD GAGAL.
  exit /b 1
)
echo.
echo BUILD SELESAI: dist\Smart_Repair_Controller_Test6.exe
endlocal
