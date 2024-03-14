#!/bin/bash
set -e
base_filename=$(basename -- "$1")
base_filename="${base_filename%.*}"
dir_path=$(dirname "$1")
magick "$1" "${dir_path}/${base_filename}.pdf"
