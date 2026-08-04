@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creation de l'environnement Python...
    py -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python -c "from app_icon import ensure_icon_files; ensure_icon_files()"
start "SP55" /B .venv\Scripts\pythonw.exe main.py
endlocal
