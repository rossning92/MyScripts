from _shutil import *

cd('~/Desktop/Youtube')
# --extract-audio --audio-format mp3
call2('youtube-dl -f bestaudio --ignore-errors {{YOUTUBE_PLAYLIST_URL}}')
