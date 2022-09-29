cd "${CWD}"
pwd
read -p 'continue?'

find . -type f -exec dos2unix {} \;
