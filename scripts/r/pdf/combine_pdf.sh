#!/bin/bash

unset MSYS_NO_PATHCONV

out_file="$HOME/Downloads/combined.pdf"

rm -f "$bookmarks_file" "$out_file"

declare -a files=("$@")
echo "${files[@]}"

pdftk "${files[@]}" cat output - |
    pdftk - output "$out_file"
