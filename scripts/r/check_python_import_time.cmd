@echo off

@REM https://github.com/nschloe/tuna
pip install tuna

python -X importtime "%~dp0..\..\bin\start_script.py" >"%TEMP%\importtime.txt" 2>&1
tuna "%TEMP%\importtime.txt"
