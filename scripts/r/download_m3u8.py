import os

from _shutil import call_echo, cd, get_clip, get_cur_time_str

if __name__ == "__main__":
    url = get_clip()

    cd(os.path.expanduser("~/Desktop"))

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
        ],
        shell=False,
    )
