@echo off
setlocal enableextensions
rem ============================================================================
rem  demarrer-flexosuite.bat - Lance l'application (double-clic)
rem ----------------------------------------------------------------------------
rem  Applique les migrations, demarre le backend FastAPI qui sert AUSSI le front
rem  (meme port), puis ouvre le navigateur. Fermer cette fenetre arrete
rem  l'application.
rem
rem  Mode sans navigateur (service / demarrage auto) :
rem      demarrer-flexosuite.bat service
rem ============================================================================
call "%~dp0_env.bat"

set "SANS_NAVIGATEUR=0"
if /i "%~1"=="service" set "SANS_NAVIGATEUR=1"
if /i "%~1"=="--sans-navigateur" set "SANS_NAVIGATEUR=1"

if not exist "%PY%" (
  echo [ERREUR] Package incomplet : %PY% introuvable. Lancez d'abord installer.bat.
  if "%SANS_NAVIGATEUR%"=="0" pause
  exit /b 1
)
if not exist "%DATA_DIR%" (
  echo [ERREUR] Donnees absentes. Lancez d'abord installer.bat.
  if "%SANS_NAVIGATEUR%"=="0" pause
  exit /b 1
)
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

rem --- Garde-fou anti double-lancement : port occupe = appli deja demarree
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo(
  echo L'application tourne deja ^(port %PORT% deja utilise^).
  if "%SANS_NAVIGATEUR%"=="1" exit /b 0
  echo Ouverture du navigateur sur http://127.0.0.1:%PORT%/
  start "" "http://127.0.0.1:%PORT%/"
  pause
  exit /b 0
)

echo(
echo === FlexoSuite ===
echo   Adresse locale : http://127.0.0.1:%PORT%/
if /i not "%HOST%"=="127.0.0.1" echo   Adresse reseau : http://^<IP-du-serveur^>:%PORT%/   ^(voir le pare-feu dans README.txt^)
echo   Donnees        : %DATA_DIR%
echo   ( Fermer cette fenetre arrete l'application. )
echo(

rem --- Migrations (idempotent) ----------------------------------------------
pushd "%BACKEND_DIR%"
"%PY%" -m alembic upgrade head 1>>"%LOG_DIR%\migrations.log" 2>&1
if not "%ERRORLEVEL%"=="0" (
  echo [ERREUR] Migrations en echec - voir %LOG_DIR%\migrations.log
  popd
  if "%SANS_NAVIGATEUR%"=="0" pause
  exit /b 1
)

rem --- Navigateur (helper en arriere-plan) ----------------------------------
if "%SANS_NAVIGATEUR%"=="0" start "FlexoSuite navigateur" /b "%APP_DIR%\open-when-ready.bat" %PORT%

rem --- Backend : API + front sur le MEME port -------------------------------
"%PY%" -m uvicorn app.main:app --host %HOST% --port %PORT%
set "RC=%ERRORLEVEL%"
popd

endlocal
exit /b %RC%
