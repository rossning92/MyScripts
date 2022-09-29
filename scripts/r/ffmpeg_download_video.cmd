@echo off
cd /d "%USERPROFILE%\Desktop"
ffmpeg -i %VIDEO_URL% -c:v copy -c:a copy output.mp4