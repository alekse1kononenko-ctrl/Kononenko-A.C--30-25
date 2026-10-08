Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
if (-not $env:PYTHON_EXE) { $env:PYTHON_EXE = 'python' }
$env:PR13_DIR = '/docs'
foreach ($case in @('stage4_ok', 'stage5_ok', 'stage5_error')) {
    & $env:PYTHON_EXE -m src.main --vfs data/deep.zip `
        --script "scripts/$case.txt"
}
Get-ChildItem -LiteralPath scripts/errors -Filter '*.txt' | ForEach-Object {
    & $env:PYTHON_EXE -m src.main --vfs data/deep.zip --script $_.FullName
}
