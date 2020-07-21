from _shutil import *

url = get_clip()
# if not url.endswith('.m3u8'):
#     sys.exit(1)

chdir(expanduser("~/Desktop"))

call_echo(
    [
        "ffmpeg",
        "-protocol_whitelist",
        "file,http,https,tcp,tls,crypto",
        "-i",
        url,
        "-c",
        "copy",
        "%s.mp4" % get_cur_time_str(),
    ], shell=False
)
