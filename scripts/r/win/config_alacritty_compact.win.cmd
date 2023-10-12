@ECHO OFF

@REM Install JetBrains Mono font
choco install jetbrainsmono

COPY "%~dp0..\..\..\settings\alacritty-compact.yml" %APPDATA%\alacritty\alacritty.yml
