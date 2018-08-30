ffmpeg -i output2.mp4 -filter_complex "[0:v] fps=12,scale=w=480:h=-1,split [a][b];[a] pa
lettegen=stats_mode=single [p];[b][p] paletteuse=new=1" StickAroundPerFrame.gif