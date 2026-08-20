<#
    build-package.ps1 - Assemble le package Windows autonome de FlexoSuite.

    Produit un zip qui contient tout ce dont le client a besoin : un Python
    embarque, les dependances runtime, le front en export statique, le backend
    et les scripts double-clic. Rien a installer sur son serveur.

    A lancer depuis un poste de developpement (Node requis pour builder le front).
#>
[CmdletBinding()]
param(
    [string]$Cache = "$PSScriptRoot\.cache",
    [string]$PythonVersion = "3.13.5",
    # Au-dela, la decompression echoue sur certains postes Windows (0x80010135).
    [int]$LongueurCheminMax = 150
)

$ErrorActionPreference = "Stop"
function Etape($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Ok($m) { Write-Host "    $m" -ForegroundColor Green }

$RacineDepot = (Resolve-Path "$PSScriptRoot\..\..").Path
$Staging = "$PSScriptRoot\staging\FlexoSuite"
$Dist = "$PSScriptRoot\dist"

# --- Version du package -----------------------------------------------------
Push-Location $RacineDepot
$Commit = (git rev-parse --short HEAD).Trim()
$Sale = (git status --porcelain)
Pop-Location
$Version = (Get-Date -Format "yyyyMMdd-HHmm") + "-$Commit"
if ($Sale) {
    # Un arbre sale ne doit jamais laisser croire que le package correspond
    # exactement au commit.
    $Version += "-modifie"
    Write-Warning "Arbre de travail modifie : la version portera le suffixe -modifie."
}

# --- Nettoyage du staging ---------------------------------------------------
if (Test-Path "$PSScriptRoot\staging") { Remove-Item -Recurse -Force "$PSScriptRoot\staging" }
New-Item -ItemType Directory -Force -Path $Staging, $Dist, $Cache | Out-Null

# --- 1. Python embarque -----------------------------------------------------
Etape "1/7 - Python embarque"
$ZipPy = Join-Path $Cache "python-$PythonVersion-embed-amd64.zip"
if (-not (Test-Path $ZipPy)) {
    $url = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
    Ok "telechargement $url"
    Invoke-WebRequest -Uri $url -OutFile $ZipPy
}
$DirPy = Join-Path $Staging "python"
Expand-Archive -Path $ZipPy -DestinationPath $DirPy -Force
# Activer site-packages : decommenter "#import site" dans pythonXY._pth
Get-ChildItem "$DirPy\python*._pth" | ForEach-Object {
    (Get-Content $_.FullName) -replace '^#\s*import site', 'import site' | Set-Content $_.FullName
}
$Py = Join-Path $DirPy "python.exe"
Ok "Python $PythonVersion pret"

# --- 2. pip -----------------------------------------------------------------
Etape "2/7 - pip"
$GetPip = Join-Path $Cache "get-pip.py"
if (-not (Test-Path $GetPip)) {
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip
}
& $Py $GetPip --no-warn-script-location -q
if ($LASTEXITCODE -ne 0) { throw "installation de pip en echec." }
Ok "pip installe"

# --- 3. Dependances runtime (sans les tests) --------------------------------
Etape "3/7 - Dependances runtime"
$Req = Get-Content (Join-Path $RacineDepot "backend\requirements.txt")
$RuntimeSeul = @()
foreach ($ligne in $Req) {
    if ($ligne -match '^\s*#\s*Tests') { break }   # on s'arrete au marqueur
    $RuntimeSeul += $ligne
}
$FichierReq = Join-Path $Cache "requirements-runtime.txt"
$RuntimeSeul | Set-Content $FichierReq -Encoding ascii
# --no-compile : pas de .pyc, donc pas de chemins interminables a la
# decompression (piege deja paye sur un autre package).
& $Py -m pip install --no-warn-script-location --no-compile -q -r $FichierReq
if ($LASTEXITCODE -ne 0) { throw "pip install des dependances en echec." }
Get-ChildItem -Path $DirPy -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Ok "Dependances runtime installees, sans bytecode"

# --- 4. Verification des imports natifs -------------------------------------
Etape "4/7 - Verification des imports"
# Un wheel manquant ne se voit qu'a l'execution, chez le client, hors ligne.
# On l'attrape ici, pas la-bas.
& $Py -c "import fastapi, uvicorn, sqlalchemy, alembic, pydantic; print('imports OK')"
if ($LASTEXITCODE -ne 0) { throw "un module ne s'importe pas dans le Python embarque." }
Ok "Tous les modules s'importent"

# --- 5. Front : export statique ---------------------------------------------
Etape "5/7 - Front (export statique)"
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm introuvable (Node requis pour builder le front)."
}
$DirFront = Join-Path $RacineDepot "frontend"
Push-Location $DirFront
try {
    Ok "npm ci..."
    & npm ci
    if ($LASTEXITCODE -ne 0) { throw "npm ci en echec." }
    $env:NEXT_OUTPUT = "export"
    # On RETIRE explicitement NEXT_PUBLIC_API_URL : la base d'API doit rester
    # VIDE, donc relative, donc servie par le backend. C'est ce qui rend le
    # mono-port possible. Une chaine vide serait traitee comme "non definie".
    Remove-Item Env:\NEXT_PUBLIC_API_URL -ErrorAction SilentlyContinue
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build en echec." }
} finally {
    Remove-Item Env:\NEXT_OUTPUT -ErrorAction SilentlyContinue
    Pop-Location
}
$Out = Join-Path $DirFront "out"
if (-not (Test-Path (Join-Path $Out "index.html"))) { throw "Export front introuvable (out\index.html)." }
Copy-Item -Recurse -Force $Out (Join-Path $Staging "web")
Ok "Front exporte -> web/"

# --- 6. Backend + scripts ---------------------------------------------------
Etape "6/7 - Backend + scripts"
$argsRobocopy = @(
    (Join-Path $RacineDepot 'backend'), (Join-Path $Staging 'backend'),
    "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
    "/XD", ".venv", "venv", "__pycache__", "tests", ".pytest_cache",
    "/XF", "*.db", "*.db-journal", "*.sqlite", "*.pyc", ".env"
)
$rc = Start-Process robocopy -ArgumentList $argsRobocopy -Wait -PassThru -NoNewWindow
if ($rc.ExitCode -ge 8) { throw "robocopy backend en echec (code $($rc.ExitCode))." }

$scripts = @(
    "_env.bat", "installer.bat", "demarrer-flexosuite.bat", "open-when-ready.bat",
    "mettre-a-jour.bat", "installer-service.bat", "reinitialiser-mot-de-passe.bat",
    "README.txt"
) | ForEach-Object { Join-Path $PSScriptRoot $_ }
Copy-Item -Force $scripts $Staging
"$Version" | Set-Content (Join-Path $Staging "VERSION.txt") -Encoding ascii
Ok "Backend + scripts copies"

# --- 7. Controle des chemins, puis archive ----------------------------------
Etape "7/7 - Controle des chemins et archive"
$prefixe = $Staging.Length + 1
$tropLongs = Get-ChildItem -Path $Staging -Recurse -File |
    Where-Object { ($_.FullName.Length - $prefixe) -gt $LongueurCheminMax }
if ($tropLongs) {
    # On echoue ICI plutot que chez le client, ou l'erreur est 0x80010135 et
    # ne dit rien.
    $tropLongs | Select-Object -First 5 | ForEach-Object {
        Write-Host "    trop long : $($_.FullName.Substring($prefixe))" -ForegroundColor Red
    }
    throw "$($tropLongs.Count) chemin(s) interne(s) depassent $LongueurCheminMax caracteres."
}
Ok "Aucun chemin interne au-dela de $LongueurCheminMax caracteres"

$Zip = Join-Path $Dist "FlexoSuite-$Version.zip"
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Compress-Archive -Path $Staging -DestinationPath $Zip
$TailleMo = [math]::Round((Get-Item $Zip).Length / 1MB, 1)
Ok "Archive : $Zip ($TailleMo Mo)"

Write-Host "`n=== Package pret ===" -ForegroundColor Green
Write-Host "  $Zip"
Write-Host "  Dezippez, puis : installer.bat  ->  demarrer-flexosuite.bat"
