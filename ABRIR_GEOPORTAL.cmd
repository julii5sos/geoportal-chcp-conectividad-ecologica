@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\abrir_geoportal_local.ps1"
if errorlevel 1 (
  echo.
  echo No se pudo iniciar el Geoportal. Revise el mensaje anterior.
  pause
)
endlocal
