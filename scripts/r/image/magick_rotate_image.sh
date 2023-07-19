#!/bin/bash
mkdir -p out
for file in "$@"; do
    echo "Rotate image: $file"
    base=$(dirname "$file")
    name=$(basename "$file")
    mkdir -p "$base/out"
    magick "$file" -rotate 90 "$base/out/$name"
done
