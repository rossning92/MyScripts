@ECHO OFF
CALL "%USERPROFILE%\.venv\myscripts\Scripts\activate.bat"
python "%~dp0start_script.py" %*
