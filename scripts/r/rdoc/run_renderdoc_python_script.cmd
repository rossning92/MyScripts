@REM https://renderdoc.org/docs/python_api/examples/renderdoc_intro.html
@ECHO OFF

set "PYTHONPATH=%USERPROFILE%\Projects\renderdoc\x64\Development\pymodules;%PYTHONPATH%"
set "PATH=%USERPROFILE%\Projects\renderdoc\x64\Development;%PATH%"

@REM "You must use exactly the same version of python to load the module as was used to build it"
"%PYTHON36_EXECUTABLE%" %*
if %ERRORLEVEL% GEQ 1 EXIT /B 1