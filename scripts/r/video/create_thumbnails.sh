ffmpeg -i $1 -vf fps=1/10,scale=-2:720 thumbnail-%03d.jpg
