zipfile=$([ $# -eq 1 ] && basename "${1%.*}.zip" || basename "$(pwd).zip")
zip -r "$zipfile" "$@"
