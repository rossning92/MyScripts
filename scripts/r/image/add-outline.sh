cd '/c/Users/Ross/Google Drive/vprojects/bili/pytorch/overlay'

magick pytorch-logo.png -write mpr:in -resize 200% \
    -channel A -morphology dilate disk:15 +channel \
    -fill white -colorize 100 -resize 50% mpr:in -composite pytorch-logo-outlined.png
