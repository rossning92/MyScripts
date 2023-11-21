input=$(printf " -i %s" "$@")
ffmpeg \
    $input -filter_complex hstack=$# \
    -c:v libx264 \
    -crf 23 \
    -preset veryfast \
    -y output.mp4
