set -x
cd "$(dirname "$1")"
ffmpeg -hide_banner -loglevel panic -stats -ss {{CUT_VIDEO_START}} -i "$(basename "$1")" {{f"-t {CUT_VIDEO_DURATION}" if CUT_VIDEO_DURATION else ""}} -vcodec copy -avoid_negative_ts make_zero -c:a copy "$(basename "$1").cut.mp4" -y
