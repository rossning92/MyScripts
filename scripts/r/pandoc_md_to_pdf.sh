set -e

HEADER="$(dirname "$0")/_header.tex"

# if "%~1"=="" (
# 	echo ERROR: please pass file as argument.
# 	exit /b 1
# )

cd "$(dirname "$1")"
infile=$(basename "$1")
outfile="${infile%.*}.pdf"
echo "$infile => $outfile"

pandoc "$infile" --pdf-engine=xelatex -o "$outfile" -V CJKmainfont="Source Han Serif CN" --wrap=preserve -f gfm+hard_line_breaks -V geometry=margin=1in -H "$HEADER" -V documentclass=extarticle -V fontsize=14pt

cmd /c start "$outfile"
