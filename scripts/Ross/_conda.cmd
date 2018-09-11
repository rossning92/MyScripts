if exist %USERPROFILE%\AppData\Local\Continuum\anaconda3 (
    set PATH=%USERPROFILE%\AppData\Local\Continuum\anaconda3\Scripts;%PATH%
	exit /b 0
)

if exist C:\tools\miniconda3 (
	set PATH=C:\tools\miniconda3\Scripts;%PATH%
	exit /b 0
)

exit /b 1