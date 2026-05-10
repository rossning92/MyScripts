#!/bin/bash
set -e

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 file1.mp4 file2.mp4 ..."
    exit 1
fi

OUTPUT="output.mp4"

# Create a temporary file list
FILELIST=$(mktemp)
for f in "$@"; do
    # Use absolute path and escape special characters for the concat demuxer
    ABS_PATH=$(realpath "$f")
    ESCAPED_PATH="${ABS_PATH//\\/\\\\}"
    ESCAPED_PATH="${ESCAPED_PATH//\'/\\\'}"
    echo "file '$ESCAPED_PATH'" >> "$FILELIST"
    echo "inpoint 0" >> "$FILELIST"
    echo "outpoint 20" >> "$FILELIST"
done

echo "Concatenating files into $OUTPUT..."
ffmpeg -y -f concat -safe 0 -i "$FILELIST" -c copy "$OUTPUT"

rm "$FILELIST"
echo "Done -> $OUTPUT"
