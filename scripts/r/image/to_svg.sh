if ! [ -x "$(command -v rsvg-convert)" ]; then
    sudo apt-get install librsvg2-bin -y
fi

cd '{{_IN_DIR}}'
mkdir -p out
for f in *.svg; do
    rsvg-convert -f svg "$f" -h {{_H}} -a -o "out/$f"
done
