selection="$(yt-dlp --list-subs "$1" | fzf)"
[ -z "$selection" ] && exit 1
lang=$(awk '{print $1}' <<<"$selection")
yt-dlp --write-sub --write-auto-sub --sub-lang "$lang" --skip-download --no-playlist "$1"
