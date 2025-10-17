input_name=$(basename "$1")
input_name=${input_name%.*}
pdfimages -j "$1" "$input_name"
