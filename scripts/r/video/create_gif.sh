cd "$(dirname "$1")"
magick -delay {{_TICKS_PER_SEC}} "${@##*/}" out.gif
