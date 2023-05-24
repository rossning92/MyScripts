# -D: display dynamic symbols
# -C: demangle the symbols
# nm -gDC "$1"

# objdump -TC "$1"

readelf -s "$1"
