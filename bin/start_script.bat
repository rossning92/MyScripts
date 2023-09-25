@ECHO OFF
CALL "%~dp0..\.venv\Scripts\activate.bat"
python "%~dp0start_script.py" %*
