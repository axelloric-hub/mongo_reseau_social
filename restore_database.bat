@echo off
rem ============================================================================
rem restore_database.bat - Remet la base dans son etat initial.
rem Vide toutes les collections puis reimporte exports\json (etat initial :
rem memes identifiants, memes dates), et recree les index.
rem A lancer apres une demonstration. Fermez l'application avant si possible.
rem ============================================================================
setlocal
cd /d "%~dp0code"

if not exist ".venv\Scripts\python.exe" (
    echo ERREUR : environnement virtuel introuvable. Lancez d'abord run.bat une fois.
    pause
    exit /b 1
)
set "PY=%CD%\.venv\Scripts\python.exe"

echo ATTENTION : toutes les modifications faites pendant la demonstration seront perdues.
choice /C ON /M "Restaurer l'etat initial (O = oui, N = non)"
if errorlevel 2 (
    echo Restauration annulee.
    exit /b 0
)

"%PY%" scripts\restaurer.py
if errorlevel 1 (
    echo ERREUR : la restauration a echoue. Verifiez que MongoDB est demarre et que exports\json existe.
    pause
    exit /b 1
)
echo.
echo Base restauree. Vous pouvez relancer run.bat.
pause
endlocal
