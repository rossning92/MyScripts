@echo off

run_script r/ue/editor/build_ue4_editor.cmd
if %errorlevel% neq 0 exit /b %errorlevel%

run_script r/ue/editor/run_editor.py
if %errorlevel% neq 0 exit /b %errorlevel%
