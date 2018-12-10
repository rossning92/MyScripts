@echo off

call :find_python %LOCALAPPDATA%\Continuum\anaconda3
call :find_python %USERPROFILE%\anaconda3
call :find_python C:\tools\miniconda3
call :find_python %LOCALAPPDATA%\Programs\Python\Python36
call :find_python C:\Python36

exit /b 0

:find_python 
if exist "%~1" (
	echo Python found: %~1
	set "PATH=%~1;%~1\Scripts;%PATH%"
)
exit /b 0
