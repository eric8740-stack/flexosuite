@echo off
rem ============================================================================
rem  _env.bat - Resout l'environnement commun (appele par les autres scripts).
rem  A NE PAS lancer directement : "call _env.bat".
rem
rem  Principe :
rem   - CODE    = dossier du package (APP_DIR)   -> backend\ web\ python\ scripts
rem   - DONNEES = %ProgramData%\FlexoSuite       -> prod.db, app.env, logs
rem  Les mises a jour remplacent le CODE ; les DONNEES ne sont JAMAIS touchees.
rem ============================================================================

rem --- APP_DIR = dossier de ce script (racine du package), sans backslash final
set "APP_DIR=%~dp0"
if "%APP_DIR:~-1%"=="\" set "APP_DIR=%APP_DIR:~0,-1%"

rem --- Dossier DONNEES (separe du code, preserve aux mises a jour)
set "DATA_DIR=%ProgramData%\FlexoSuite"
set "APP_ENV=%DATA_DIR%\app.env"
set "LOG_DIR=%DATA_DIR%\logs"

rem --- Charge app.env s'il existe (lignes CLE=VALEUR, # = commentaire)
if exist "%APP_ENV%" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%APP_ENV%") do set "%%A=%%B"
)

rem --- Valeurs par defaut PROD (si absentes de app.env)
if not defined HOST set "HOST=127.0.0.1"
if not defined PORT set "PORT=8000"
if not defined DEMO_MODE set "DEMO_MODE=0"

rem --- Chemins derives (jamais stockes dans app.env : robustes au deplacement)
set "BACKEND_DIR=%APP_DIR%\backend"
set "FLEXO_STATIC_DIR=%APP_DIR%\web"
set "PY=%APP_DIR%\python\python.exe"
set "PYTHONDONTWRITEBYTECODE=1"

rem --- Chemin d'import : NE PAS poser PYTHONPATH ici, ce serait sans effet.
rem     Un Python EMBEDDABLE ignore PYTHONPATH des qu'un fichier ._pth existe
rem     (verifie le 20/08/2026 : sys.path n'en gardait aucune trace). Le dossier
rem     backend est donc declare dans le ._pth par build-package.ps1.
rem     Sans cela, "python -m scripts.xxx" echoue sur un ModuleNotFound alors
rem     que le module est bien livre -- alembic et uvicorn s'en sortaient chacun
rem     par leur propre mecanisme, ce qui masquait le defaut.

rem --- URL SQLite (chemin absolu Windows -> slashes pour SQLAlchemy)
set "DB_FILE=%DATA_DIR%\prod.db"
set "DB_SLASH=%DB_FILE:\=/%"
set "DATABASE_URL=sqlite:///%DB_SLASH%"

goto :eof
