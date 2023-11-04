@ECHO OFF
CALL "%USERPROFILE%\.venv\myscripts\Scripts\activate.bat"
python "%~dp0run_script.py" %*
