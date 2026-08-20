@echo off
setlocal enableextensions enabledelayedexpansion
rem ============================================================================
rem  mettre-a-jour.bat - Remplace le CODE, preserve les DONNEES
rem ----------------------------------------------------------------------------
rem  Usage : mettre-a-jour.bat "D:\chemin\du\nouveau\package"
rem          (sans argument, le chemin est demande)
rem
rem  Garantie : le dossier DONNEES (%ProgramData%\FlexoSuite) n'est jamais dans
rem  la zone remplacee. Une empreinte de la base est prise AVANT et APRES : si
rem  elle change autrement que par une migration attendue, on le voit.
rem ============================================================================
call "%~dp0_env.bat"

set "SRC=%~1"
if "%SRC%"=="" set /p "SRC=Chemin du nouveau package : "
if "%SRC%"=="" goto :annule
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"

if not exist "%SRC%\backend\app\main.py" (
  echo [ERREUR] "%SRC%" ne ressemble pas a un package FlexoSuite.
  goto :echec
)
if /i "%SRC%"=="%APP_DIR%" (
  echo [ERREUR] La source et la destination sont le meme dossier.
  goto :echec
)

echo(
echo === Mise a jour de FlexoSuite ===
echo   Depuis  : %SRC%
echo   Vers    : %APP_DIR%
echo   Donnees : %DATA_DIR%   ^(NON touchees^)
echo(
set /p "OK=Continuer ? (o/N) "
if /i not "%OK%"=="o" goto :annule

rem --- Empreinte AVANT -------------------------------------------------------
set "AVANT=(absente)"
if exist "%DB_FILE%" for /f "skip=1 tokens=*" %%H in ('certutil -hashfile "%DB_FILE%" SHA256') do if not defined AVANT_SET (set "AVANT=%%H" & set "AVANT_SET=1")

rem --- 1. Arret de l'application --------------------------------------------
echo [1/4] Arret de l'application...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
  for /f "tokens=1" %%N in ('tasklist /fi "PID eq %%P" /nh ^| findstr /i python') do taskkill /pid %%P /f >nul 2>&1
)
ping -n 3 127.0.0.1 >nul

rem --- 2. Remplacement du CODE ----------------------------------------------
echo [2/4] Remplacement du code...
robocopy "%SRC%" "%APP_DIR%" /MIR /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo [ERREUR] Copie du code echouee ^(robocopy^).
  goto :echec
)

rem --- 3. Copie de secours puis migrations ----------------------------------
echo [3/4] Sauvegarde de la base, puis migrations...
if exist "%DB_FILE%" copy /y "%DB_FILE%" "%DATA_DIR%\prod.avant-maj.db" >nul
pushd "%BACKEND_DIR%"
"%PY%" -m alembic upgrade head
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" (
  echo [ERREUR] Migrations en echec. La base d'avant est dans :
  echo          %DATA_DIR%\prod.avant-maj.db
  goto :echec
)

rem --- 4. Verdict ------------------------------------------------------------
echo [4/4] Verification...
set "APRES=(absente)"
if exist "%DB_FILE%" for /f "skip=1 tokens=*" %%H in ('certutil -hashfile "%DB_FILE%" SHA256') do if not defined APRES_SET (set "APRES=%%H" & set "APRES_SET=1")
if "%AVANT%"=="%APRES%" (
  echo        Base inchangee - aucune migration n'etait necessaire.
) else (
  echo        Base migree. Copie d'avant conservee : %DATA_DIR%\prod.avant-maj.db
)

echo(
echo === Mise a jour terminee ===
echo   Relancez demarrer-flexosuite.bat
echo(
endlocal
pause
exit /b 0

:annule
echo Annule - rien n'a ete modifie.
endlocal
pause
exit /b 0

:echec
echo(
echo === ECHEC de la mise a jour ===
endlocal
pause
exit /b 1
