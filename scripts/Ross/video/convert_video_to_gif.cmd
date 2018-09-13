cd /d "%USERPROFILE%\Desktop"

cd %~dp1

:: set PATH=C:\ProgramData\chocolatey\bin;%PATH%

:: Convert video to gif
::fps=25,scale=w=-1:h=480
ffmpeg -i %1 -filter_complex "[0:v] fps=15,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1" %~dpn1.gif


:: Optimize gif
magick %~dpn1.gif -coalesce -fuzz 4%% +dither -layers Optimize output_optimized.gif