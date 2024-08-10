#!/bin/bash

unset MSYS_NO_PATHCONV

declare -a files=("$@")
echo "${files[@]}"

dir_of_first_file=$(dirname "${files[0]}")
out_file="${dir_of_first_file}/combined.pdf"

pdftk "${files[@]}" cat output - |
    pdftk - output "$out_file"
