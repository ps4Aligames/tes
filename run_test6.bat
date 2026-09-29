@echo off
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python tidak ditemukan.
  pause
  exit /b 1
)
py smart_repair_controller_test6.py
