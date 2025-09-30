#!/bin/sh
set -e

input="$1"
output="${input%.*}.jpg"

magick "$input" -quality 100 "$output"
