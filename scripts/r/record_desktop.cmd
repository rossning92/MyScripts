@echo off
setlocal
cd /d %USERPROFILE%\Desktop
ffmpeg -f gdigrab -framerate 60 -i desktop -c:v libx264 -crf 0 -preset ultrafast output.mkv