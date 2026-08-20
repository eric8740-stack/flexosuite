@echo off
setlocal enableextensions
rem ============================================================================
rem  reinitialiser-mot-de-passe.bat - Repart d'un mot de passe administrateur
rem ----------------------------------------------------------------------------
rem  POURQUOI CE SCRIPT EXISTE : le mot de passe n'est stocke que HACHE. Sans lui,
rem  un mot de passe perdu bloque le client, et il faut intervenir a la main dans
rem  la base. Ce manque a ete constate le 20/08/2026 sur le squelette de
rem  livraison de reference ; il ne devait pas etre reproduit ici.
rem
rem  Ce script ne touche QUE le compte administrateur. Aucune donnee metier n'est
rem  modifiee, aucune base n'est recreee.
rem ============================================================================
call "%~dp0_env.bat"

echo(
echo === Reinitialisation du mot de passe administrateur ===
echo   Base : %DB_FILE%
echo(

if not exist "%PY%" (
  echo [ERREUR] Package incomplet : %PY% introuvable.
  goto :echec
)
if not exist "%DB_FILE%" (
  echo [ERREUR] Aucune base a %DB_FILE% - lancez d'abord installer.bat.
  goto :echec
)

rem --- L'application doit etre arretee : sinon la session en cours resterait
rem     valide avec l'ancien mot de passe.
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [ERREUR] L'application tourne encore ^(port %PORT%^).
  echo          Fermez sa fenetre, puis relancez ce script.
  goto :echec
)

pushd "%BACKEND_DIR%"
"%PY%" -m scripts.reinitialiser_admin
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" goto :echec

echo(
echo === Termine ===
echo   Relancez demarrer-flexosuite.bat, puis connectez-vous avec le nouveau
echo   mot de passe. Changez-le depuis l'application.
echo(
endlocal
pause
exit /b 0

:echec
echo(
echo === ECHEC ===
endlocal
pause
exit /b 1
