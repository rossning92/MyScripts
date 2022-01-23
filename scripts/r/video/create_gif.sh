cd "${_CUR_DIR}"

magick -delay {{_TICKS_PER_SEC}} *.png out.gif
