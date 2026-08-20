@echo off
rem ============================================================================
rem  open-when-ready.bat [PORT] - Ouvre le navigateur quand le backend repond.
rem  Lance en arriere-plan par demarrer-flexosuite.bat. Outils natifs uniquement.
rem ============================================================================
setlocal
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"
set "URL=http://127.0.0.1:%PORT%/"
where curl >nul 2>&1
if errorlevel 1 goto :attendre
for /l %%i in (1,1,60) do (
  curl -s -o nul "%URL%api/sante" && goto :ouvrir
  ping -n 2 127.0.0.1 >nul
)
goto :ouvrir
:attendre
ping -n 5 127.0.0.1 >nul
:ouvrir
start "" "%URL%"
endlocal
