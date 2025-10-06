#!/usr/bin/env bash

read -p "Start time (e.g. 1:00): " inTime
read -p "Duration in seconds (e.g. 10): " duration

input="$1"
output="${input}.out.mp4"

ffmpeg -hide_banner -loglevel panic \
	-ss "$inTime" \
	-i "$input" \
	-t "$duration" \
	-c:v libx264 -crf 19 -preset slow -pix_fmt yuv420p \
	-c:a aac \
	"$output"
