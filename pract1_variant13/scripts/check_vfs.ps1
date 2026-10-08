Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
if (-not $env:PYTHON_EXE) { $env:PYTHON_EXE = 'python' }
& $env:PYTHON_EXE scripts/create_vfs.py
$env:PR13_DIR = '/docs'
foreach ($case in @('minimal', 'several', 'deep')) {
    & $env:PYTHON_EXE -m src.main --vfs "data/$case.zip" `
        --script scripts/vfs_smoke.txt
}
& $env:PYTHON_EXE -m src.main --vfs data/missing.zip `
    --script scripts/vfs_smoke.txt
& $env:PYTHON_EXE -m src.main --vfs data/invalid.zip `
    --script scripts/vfs_smoke.txt
