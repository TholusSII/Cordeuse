@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Environnement Python introuvable.
    echo Lance d'abord lancer_cordeuse.bat pour creer .venv et installer les dependances.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" serial_proxy.py
if errorlevel 1 pause
