@echo off
setlocal
cd /d %USERPROFILE%\Desktop

ffmpeg -f gdigrab -framerate 60 -offset_x 0 -offset_y 0 -video_size 1920x1080 -draw_mouse 1 -i desktop -c:v libx264 -r 60 -preset ultrafast -pix_fmt yuv420p -y "output.mp4"
