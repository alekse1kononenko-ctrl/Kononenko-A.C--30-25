@echo off
cd /d "%~dp0pract1_variant13"
if not defined PYTHON_EXE set "PYTHON_EXE=python"
"%PYTHON_EXE%" -m src.main %*
