@echo off
cd /d "%~dp0.."
if not defined PYTHON_EXE set "PYTHON_EXE=python"
"%PYTHON_EXE%" scripts/create_vfs.py
set "PR13_DIR=/docs"
for %%V in (minimal several deep) do (
    call run.bat --vfs data/%%V.zip --script scripts/stage3_ok.txt
)
call run.bat --vfs data/missing.zip --script scripts/stage3_ok.txt
call run.bat --vfs data/invalid.zip --script scripts/stage3_ok.txt
