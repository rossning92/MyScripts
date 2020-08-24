cd "C:\Users\Ross\Google Drive\KidslogicVideo\ep21\animation"

magick "unity-512.webp" \
    \( "unity-512.webp" -alpha extract \) \
    -matte -bordercolor none -border 100x100 \
    -alpha off -compose copy_opacity -composite -compose over \
    \( -clone 0 -background white -shadow 400x20 \) \
    +swap \
    -background none -layers merge \
    \( +clone -alpha extract -colors 256 \) -alpha off -compose copy_opacity -composite -compose over \
    -trim \
    "output.png"
