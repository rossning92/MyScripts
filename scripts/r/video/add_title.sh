set -e

folder=$(dirname "$1")
file=$(basename "$1")

cd "$folder"
mkdir -p out

text=$(<label.txt)

ffmpeg -i "$1" -filter_complex "[0:v]pad=iw:ih+50:0:50:color=white, drawtext=text='${text}':fix_bounds=true:fontfile=/Windows/Fonts/arial.ttf:fontsize=18:fontcolor=black:x=(w-tw)/2:y=(50-th)/2" "out/$file" -y
