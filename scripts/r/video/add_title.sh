set -e

folder=$(dirname "$1")
cd "$folder"
mkdir -p out

file=$(basename "$1")
text="${file}"
text="${text%.*}"   # remove extension
text="${text//_/ }" # replace underscore with space

ffmpeg -i "$1" -filter_complex "[0:v]drawtext=text='${text}':bordercolor=black:borderw=4:fix_bounds=true:fontfile=/Windows/Fonts/arial.ttf:fontsize=48:fontcolor=white:x=48:y=48" "out/$file" -y
