@echo off
setlocal enableextensions
rem ============================================================================
rem  installer-service.bat - Demarrage automatique au boot (optionnel)
rem ----------------------------------------------------------------------------
rem  Cree une tache planifiee qui lance l'application au demarrage du serveur,
rem  sans fenetre et sans navigateur. A lancer EN ADMINISTRATEUR.
rem
rem  Piege connu : la tache tourne sous le compte SYSTEME. Si vos donnees ou vos
rem  fichiers d'import vivent sur un partage reseau, SYSTEME n'y a pas acces —
rem  utilisez alors un compte de service dedie.
rem ============================================================================
call "%~dp0_env.bat"

net session >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] Lancez ce script en tant qu'administrateur ^(clic droit^).
  pause
  exit /b 1
)

set "TACHE=FlexoSuite"
schtasks /query /tn "%TACHE%" >nul 2>&1
if not errorlevel 1 (
  echo La tache "%TACHE%" existe deja : elle est remplacee.
  schtasks /delete /tn "%TACHE%" /f >nul
)

schtasks /create /tn "%TACHE%" /tr "\"%APP_DIR%\demarrer-flexosuite.bat\" service" /sc onstart /ru SYSTEM /rl HIGHEST /f
if errorlevel 1 (
  echo [ERREUR] Creation de la tache planifiee en echec.
  pause
  exit /b 1
)

echo(
echo === Demarrage automatique active ===
echo   L'application se lancera au prochain demarrage du serveur.
echo   Pour la lancer tout de suite : schtasks /run /tn "%TACHE%"
echo   Pour desactiver              : schtasks /delete /tn "%TACHE%" /f
echo(
endlocal
pause
exit /b 0
