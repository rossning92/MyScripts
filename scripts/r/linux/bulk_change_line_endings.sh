cd "${_CUR_DIR}"
pwd
read -p 'continue?'

find . -type f -exec dos2unix {} \;
