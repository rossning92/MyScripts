#!/usr/bin/env bash
set -e
cd "$(dirname "$1")"
start="{{CUT_VIDEO_START}}"
duration="{{CUT_VIDEO_DURATION}}"
filename="$(basename "$1")"
name_without_ext="${filename%.*}"
base_output="${name_without_ext}_cut"
output="${base_output}.mp4"
counter=2
while [ -e "$output" ]; do
	output="${base_output}${counter}.mp4"
	counter=$((counter + 1))
done

ffmpeg -hide_banner -loglevel panic \
	-ss "$start" \
	-i "$filename" \
	-t "$duration" \
	-c:v libx264 -crf 19 -preset slow -pix_fmt yuv420p \
	-c:a aac \
	"$output"
