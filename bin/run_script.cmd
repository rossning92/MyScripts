@ECHO OFF
CALL "%~dp0..\.venv\Scripts\activate.bat"
python "%~dp0run_script.py" %*
