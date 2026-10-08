@echo off
cd /d "%~dp0.."
set "PR13_DIR=/docs"
call run.bat --vfs data/deep.zip --script scripts/stage4_ok.txt
call run.bat --vfs data/deep.zip --script scripts/stage5_ok.txt
call run.bat --vfs data/deep.zip --script scripts/stage5_error.txt
for %%S in (scripts/errors/*.txt) do (
    call run.bat --vfs data/deep.zip --script "scripts/errors/%%~nxS"
)
