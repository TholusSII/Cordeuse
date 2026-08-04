@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python -c "from app_icon import ensure_icon_files; ensure_icon_files()"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$desktop=[Environment]::GetFolderPath('Desktop');" ^
  "$shell=New-Object -ComObject WScript.Shell;" ^
  "$shortcut=$shell.CreateShortcut((Join-Path $desktop 'Cordeuse SP55.lnk'));" ^
  "$shortcut.TargetPath=(Resolve-Path '.venv\Scripts\pythonw.exe').Path;" ^
  "$shortcut.Arguments='""' + (Resolve-Path 'main.py').Path + '""';" ^
  "$shortcut.WorkingDirectory=(Resolve-Path '.').Path;" ^
  "$shortcut.IconLocation=(Resolve-Path 'sp55_logo.ico').Path + ',0';" ^
  "$shortcut.Description='Cordeuse de raquettes SP55';" ^
  "$shortcut.Save()"

echo.
echo Raccourci "Cordeuse SP55" cree sur le Bureau.
pause
endlocal
