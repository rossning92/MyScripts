# -D: display dynamic symbols
nm -gDC "$1" | grep " T "
