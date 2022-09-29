@echo off
setlocal

set VCBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\VC\Auxiliary\Build"
if exist %VCBUILD% goto :BUILD

echo Cannot find Visual C++ Build Tools.
exit /b 1

:BUILD
call %VCBUILD%\vcvarsall.bat x86 
cl.exe /EHsc %1
del %~dpn1.obj
if not %errorlevel%==0 exit /b 1

%~dpn1.exe
if not %errorlevel%==0 exit /b 1
