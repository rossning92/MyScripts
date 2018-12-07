@echo off
setlocal

set TARGET=cmd2exe

set PATH=C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build;%PATH%
call vcvarsall.bat x86_amd64

cl /nologo /EHsc /MD /O1 /GL /Fo"%TEMP%\%TARGET%.obj" src.cpp /link /out:"..\..\..\bin\%TARGET%.exe"
