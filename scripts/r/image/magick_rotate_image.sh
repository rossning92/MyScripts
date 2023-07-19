#!/bin/bash
mkdir -p out
for file in "$@"; do
    echo "Rotate image: $file"
    magick "$file" -rotate 90 "out/$file"
done
