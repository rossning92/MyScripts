from _shutil import call_echo, cd

if __name__ == "__main__":
    cd("~/Desktop/Youtube")
    # --extract-audio --audio-format mp3
    call_echo(
        "yt-dlp --cookies youtube-cookies.txt -f best[height=720] --ignore-errors {{YOUTUBE_PLAYLIST_URL}}"
    )
