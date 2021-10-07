@echo off

:: Python36
call :find_python %LOCALAPPDATA%\Programs\Python\Python36
if %errorlevel%==0 exit /b 0

call :find_python C:\Python38
if %errorlevel%==0 exit /b 0

call :find_python C:\Python36
if %errorlevel%==0 exit /b 0

:: Anaconda
call :find_python %LOCALAPPDATA%\Continuum\anaconda3
if %errorlevel%==0 exit /b 0

call :find_python %USERPROFILE%\anaconda3
if %errorlevel%==0 exit /b 0

call :find_python C:\tools\Anaconda3
if %errorlevel%==0 (
	call activate.bat
	exit /b 0
)

call :find_python C:\tools\miniconda3
if %errorlevel%==0 (
	call activate.bat
	exit /b 0
)

exit /b 1


:find_python 
if exist "%~1" (
	echo Python found: %~1
	set "PATH=%~1;%~1\Scripts;%PATH%"
	exit /b 0
) else (
	exit /b 1
)
