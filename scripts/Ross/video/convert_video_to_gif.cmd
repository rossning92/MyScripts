cd /d "%USERPROFILE%\Desktop"

set INPUT=output.mp4

:: set PATH=C:\ProgramData\chocolatey\bin;%PATH%

:: Convert video to gif
ffmpeg -i %INPUT% -filter_complex "[0:v] fps=25,scale=w=480:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1" output.gif


:: Optimize gif
magick output.gif -coalesce -fuzz 4% +dither -layers Optimize output_optimized.gif