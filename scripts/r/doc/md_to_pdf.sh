# --border-top=1mm --border-bottom=1mm
mdpdf --style="$(dirname "$(realpath "$0")")/style.css" --format=Letter "$1"
