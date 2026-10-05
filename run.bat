@echo off
rem ============================================================================
rem run.bat - Lance l'application (MongoDB + API Django + interface Streamlit).
rem Verifie Python, cree l'environnement virtuel, installe les dependances,
rem controle MongoDB, genere les donnees si la base est vide, puis demarre.
rem ============================================================================
setlocal
cd /d "%~dp0code"

where python >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python est introuvable. Installez Python 3.10 ou plus recent depuis python.org
    echo et cochez "Add python.exe to PATH" pendant l'installation.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
    if errorlevel 1 (
        echo ERREUR : creation de l'environnement virtuel impossible.
        pause
        exit /b 1
    )
)
set "PY=%CD%\.venv\Scripts\python.exe"

if not exist ".env" copy ".env.example" ".env" >nul

if not exist ".venv\dependances_ok.txt" (
    echo Installation des dependances ^(premiere fois uniquement^)...
    "%PY%" -m pip install --upgrade pip >nul
    "%PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERREUR : installation des dependances impossible. Verifiez la connexion Internet.
        pause
        exit /b 1
    )
    echo ok> ".venv\dependances_ok.txt"
)

echo Verification de MongoDB...
"%PY%" scripts\verifier_mongo.py
set "CODE=%errorlevel%"
if "%CODE%"=="1" (
    echo.
    echo MongoDB ne repond pas. Demarrez le service MongoDB ^(ou verifiez MONGODB_URI dans code\.env^)
    echo puis relancez run.bat.
    pause
    exit /b 1
)
if "%CODE%"=="2" (
    echo Generation du jeu de donnees initial ^(une seule fois^)...
    "%PY%" generer_donnees.py
    if errorlevel 1 (
        echo ERREUR : la generation des donnees a echoue.
        pause
        exit /b 1
    )
)

rem Evite la question "email" de Streamlit au premier lancement
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
    > "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
    >> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

echo Demarrage de l'API Django sur http://127.0.0.1:8000 ...
start "API Django - ne pas fermer" cmd /k ""%PY%" backend\manage.py runserver 8000 --noreload"
timeout /t 4 /nobreak >nul

echo Demarrage de l'interface Streamlit ^(le navigateur va s'ouvrir^)...
echo Connexion de demonstration : valdez_237 / 1234
"%PY%" -m streamlit run frontend\app.py
endlocal
