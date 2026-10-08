Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$env:PR13_DIR = '/docs'
if (-not $env:PYTHON_EXE) { $env:PYTHON_EXE = 'python' }
& $env:PYTHON_EXE -m src.main --vfs data/deep.zip `
    --script scripts/vfs_smoke.txt
& $env:PYTHON_EXE -m src.main --vfs 'data/path with spaces.zip' `
    --script scripts/vfs_smoke.txt
& $env:PYTHON_EXE -m src.main --vfs data/deep.zip `
    --script scripts/stage2_error.txt
& $env:PYTHON_EXE -m src.main --vfs data/deep.zip `
    --script scripts/no_such_script.txt
'exit' | & $env:PYTHON_EXE -m src.main --vfs data/deep.zip
& $env:PYTHON_EXE -m src.main --script scripts/vfs_smoke.txt
