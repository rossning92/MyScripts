cd "$CURRENT_FOLDER"
ffmpeg -r 60 -i %07d.png -vcodec prores_ks -pix_fmt yuva444p10le -alpha_bits 16 -profile:v 4444 -f mov out.mov -y
