from _shutil import *
import signal
from _video import *


def screen_record(out_file=None, max_secs=10, bit_rate="40M"):
    """
    adb shell screenrecord /sdcard/screen_record.mp4 --time-limit 5 --bit-rate 40M
    """

    TMP_RECORD_FILE = "/data/local/tmp/screen_record.mp4"

    print("Press Ctrl-C to stop recording...")

    signal.signal(signal.SIGINT, lambda a, b: None)

    if out_file is None:
        out_file = "Recording_%s.mp4" % get_cur_time_str()

    args = ["adb", "shell", "screenrecord", TMP_RECORD_FILE]
    args += ["--time-limit", "{}".format(max_secs), "--bit-rate", "{}".format(bit_rate)]
    subprocess.check_call(args)

    subprocess.check_call(["adb", "pull", TMP_RECORD_FILE, out_file])

    return out_file


if __name__ == "__main__":
    chdir("~/Desktop")

    out_file = screen_record(
        max_secs=int("{{_MAX_SECS}}") if "{{_MAX_SECS}}" else 10,
        bit_rate="{{_BIT_RATE}}" if "{{_BIT_RATE}}" else "20M",
    )

    if "{{_RESIZE_H}}":
        extra_args = ["-r", "60"]
        extra_args += ["-vf", "scale=-2:{{_RESIZE_H}}"]
        out_file = ffmpeg(out_file, out_file=out_file, extra_args=extra_args)

        shell_open(out_file)
