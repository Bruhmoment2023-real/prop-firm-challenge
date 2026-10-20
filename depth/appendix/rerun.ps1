# Rebuild paper 01's main results in order. Usage (PowerShell):
#   .\rerun.ps1 -DryRun                 # print what would run, check interpreter and imports (seconds)
#   .\rerun.ps1 -Quick                  # smoke test: validation is skipped, blocks A-C at 2,000 paths, no figures (3 minutes on a quiet laptop; 13 minutes measured on 2026-10-17 with several other jobs running)
#   .\rerun.ps1 -Full                   # real run: about 35-45 minutes of CPU on a quiet laptop, in separate parts (see code\README.md)
#   .\rerun.ps1 -Quick -Root E:\Research-Staging\01-prop-firm-challenge\rerun-test   # run on a copy so the pack's results are untouched
# Stages: 1 rule tables (needs the archived firm pages already in data\raw), 2 validation, 3 experiments A-E, 4 figures and tables.
# Web steps (fetch_pages.py, fetch_market_data.py) are NOT run: they would overwrite the dated 2026-10-13 evidence. Run them by hand only to refresh the data.
# The literature map (bibliometrics) is rebuilt separately: see ..\..\bibliometrics\README.md; its heavy steps are not run here.
param([switch]$DryRun, [switch]$Quick, [switch]$Full, [string]$Root = "D:\Research-Publishing\01-prop-firm-challenge")
$ErrorActionPreference = "Stop"
if (-not (Test-Path "D:\")) { throw "D: is missing - stopping (nothing is written to C:)." }
$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "D:\Research-Publishing\01-prop-firm-challenge\.venv\Scripts\python.exe" }
$code = Join-Path $Root "code"
function Step($name, $args_) {
    Write-Host "== $name : $py $($args_ -join ' ')"
    if (-not $DryRun) { Push-Location $Root; & $py @args_; if ($LASTEXITCODE -ne 0) { Pop-Location; throw "$name failed" }; Pop-Location }
}
Write-Host "Root: $Root"
Write-Host "Interpreter:" (& $py --version)
& $py -c "import numpy, scipy, pandas, matplotlib, numba; print('imports ok: numpy', numpy.__version__, 'numba', numba.__version__)"
if (-not ($Quick -or $Full -or $DryRun)) { Write-Host "Choose -DryRun, -Quick or -Full."; exit 0 }
Step "1 rule tables"  @("$code\build_rule_tables.py")
if ($Full) {
    Step "2 validation"   @("$code\01_validate.py")
    Step "3A part 1"      @("$code\02_run_experiments.py", "--only", "A", "--part", "1of2")
    Step "3A part 2"      @("$code\02_run_experiments.py", "--only", "A", "--part", "2of2")
    Step "3B"             @("$code\02_run_experiments.py", "--only", "B")
    Step "3C"             @("$code\02_run_experiments.py", "--only", "C")
    Step "3DE"            @("$code\02_run_experiments.py", "--only", "DE")
    Step "4 figures"      @("$code\03_figures_and_tables.py")
} elseif ($Quick) {
    Step "3 quick A-C"    @("$code\02_run_experiments.py", "--quick")
    Write-Host "Quick results are written to results\QUICK_*.csv and results\parts_quick\ and never mix with the real tables."
}
Write-Host "done."
