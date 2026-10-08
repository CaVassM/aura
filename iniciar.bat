@echo off
rem Levanta backend (8080) y frontend (3000) de AURA. Doble clic o: iniciar.bat [-SinNavegador | -Detener]
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar.ps1" %*
if errorlevel 1 pause
