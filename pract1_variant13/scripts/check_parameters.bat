@echo off
cd /d "%~dp0.."
set "PR13_DIR=/docs"
call run.bat --vfs data/deep.zip --script scripts/vfs_smoke.txt
call run.bat --vfs "data/path with spaces.zip" --script scripts/vfs_smoke.txt
call run.bat --vfs data/deep.zip --script scripts/stage2_error.txt
call run.bat --vfs data/deep.zip --script scripts/no_such_script.txt
echo exit|call run.bat --vfs data/deep.zip
call run.bat --script scripts/vfs_smoke.txt
