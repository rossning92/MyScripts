cd "$(dirname "$1")"
inputfile=$(basename "$1")

# magick "$inputfile" -compress Zip output.pdf
# pdftk "$inputfile" output output.pdf compress

if [[ "$(uname -s)" == *"MINGW"* ]]; then
    GS="C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
else
    GS=gs
fi

# https://askubuntu.com/questions/113544/how-can-i-reduce-the-file-size-of-a-scanned-pdf-file
"$GS" -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
    -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf "$inputfile"
