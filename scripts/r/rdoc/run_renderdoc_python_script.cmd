@REM https://renderdoc.org/docs/python_api/examples/renderdoc_intro.html
@ECHO OFF

set "PYTHONPATH=%USERPROFILE%\Projects\renderdoc\x64\Development\pymodules;%PYTHONPATH%"
set "PATH=%USERPROFILE%\Projects\renderdoc\x64\Development;%PATH%"

"%PYTHON36_DIR%\python.exe" %*
