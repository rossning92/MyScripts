ffmpeg -i "$1" -filter_complex "[0:v]pad=iw:ih+50:0:50:color=white, drawtext=text='{{_TITLE}}':fix_bounds=true:fontfile=/Windows/Fonts/arial.ttf:fontsize=18:fontcolor=black:x=(w-tw)/2:y=(50-th)/2" 123.mp4 -y
