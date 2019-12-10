@echo off
set PYTHON_PATH=%~dp0..\libs
python -c "from _script import *; run_script('%1')"
