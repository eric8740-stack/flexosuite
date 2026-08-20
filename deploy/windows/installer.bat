@echo off
setlocal enableextensions
rem ============================================================================
rem  installer.bat - Installation IDEMPOTENTE
rem ----------------------------------------------------------------------------
rem  Prepare le dossier DONNEES, genere app.env s'il manque, applique les
rem  migrations. NE REECRIT JAMAIS une base existante. Relancable sans risque.
rem  Le dossier DONNEES (%ProgramData%\FlexoSuite) est separe du code.
rem ============================================================================
call "%~dp0_env.bat"

echo(
echo === Installation de FlexoSuite ===
echo   Code    : %APP_DIR%
echo   Donnees : %DATA_DIR%
echo(

rem --- Verifs de base -------------------------------------------------------
if not exist "%PY%" (
  echo [ERREUR] Python embarque introuvable : %PY%
  echo          Le package est incomplet. Reassemblez-le avec build-package.ps1.
  goto :echec
)
if not exist "%BACKEND_DIR%\app\main.py" (
  echo [ERREUR] Backend introuvable : %BACKEND_DIR%\app\main.py
  goto :echec
)
if not exist "%FLEXO_STATIC_DIR%\index.html" (
  echo [ERREUR] Front builde introuvable : %FLEXO_STATIC_DIR%\index.html
  goto :echec
)

rem --- 1. Dossiers DONNEES ---------------------------------------------------
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%LOG_DIR%"  mkdir "%LOG_DIR%"
echo [1/3] Dossier donnees pret : %DATA_DIR%

rem --- 2. app.env genere seulement s'il manque ------------------------------
if exist "%APP_ENV%" (
  echo [2/3] app.env deja present : conserve tel quel - idempotent.
  goto :apres_env
)
> "%APP_ENV%" echo # Configuration FlexoSuite - poste de l'imprimerie
>>"%APP_ENV%" echo # Genere par installer.bat. Editez puis relancez demarrer-flexosuite.bat.
>>"%APP_ENV%" echo DEMO_MODE=0
>>"%APP_ENV%" echo HOST=127.0.0.1
>>"%APP_ENV%" echo PORT=8000
echo [2/3] app.env genere : aucun mot de passe en dur.
call "%~dp0_env.bat"
:apres_env

rem --- 3. Migrations (cree prod.db si absent, migre sinon - jamais efface) ---
set "BASE_EXISTAIT=1"
if not exist "%DB_FILE%" set "BASE_EXISTAIT=0"
echo [3/3] Migrations base ( %DB_FILE% )...
pushd "%BACKEND_DIR%"
"%PY%" -m alembic upgrade head
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" (
  echo [ERREUR] Les migrations ont echoue, code %RC%.
  goto :echec
)
if "%BASE_EXISTAIT%"=="0" (
  echo        Base creee et migree.
) else (
  echo        Base existante migree - donnees preservees.
)

echo(
echo === Installation terminee ===
echo   Lancer l'application : double-clic sur demarrer-flexosuite.bat
echo   Demarrage automatique au boot ^(optionnel^) : installer-service.bat
echo   Mot de passe administrateur perdu : reinitialiser-mot-de-passe.bat
echo(
endlocal
pause
exit /b 0

:echec
echo(
echo === ECHEC de l'installation ===
endlocal
pause
exit /b 1
