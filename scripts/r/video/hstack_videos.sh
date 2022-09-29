input=
for i in "$@"; do
    input="$input -i $i"
done

ffmpeg \
    $input -filter_complex hstack=$# \
    -c:v libx264 \
    -crf 23 \
    -preset veryfast \
    -y output.mp4
