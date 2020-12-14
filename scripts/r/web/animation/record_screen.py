from _shutil import *
from _term import *
import keyboard

TEMP_FILE = os.path.join(gettempdir(), "screen-record.mp4")

__ps_recorder = None


region = None


def set_region(rect):
    global region
    region = rect


def start_record():
    global __ps_recorder
    if __ps_recorder is not None:
        return

    args = [
        "captura-cli",
        "start",
        "--speaker=4",
        "--cursor",
        "-r",
        "60",
        "--vq",
        "100",
        "-f",
        TEMP_FILE,
        "-y",
    ]

    if region is not None:
        args += [
            "--source",
            ",".join(["%d" % x for x in region]),
        ]

    __ps_recorder = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )

    while True:
        line = __ps_recorder.stdout.readline().decode()
        # print(line)
        if "Press p" in line:
            print2("Recording started.", color="green")
            minimize_cur_terminal()
            break


def stop_record():
    global __ps_recorder
    if __ps_recorder is None:
        return

    __ps_recorder.stdin.write(b"q")
    __ps_recorder.stdin.close()
    __ps_recorder.wait()
    print2("Recording stopped.", color="green")
    __ps_recorder = None


def save_record(file, overwrite=False):
    file = os.path.realpath(file)
    assert os.path.exists(TEMP_FILE)
    os.makedirs(os.path.dirname(file), exist_ok=True)

    if overwrite and os.path.exists(file):
        os.remove(file)

    os.rename(TEMP_FILE, file)


def play_record():
    call_echo(["mpv", TEMP_FILE])


if __name__ == "__main__":
    out_dir = os.path.join(os.environ["VIDEO_PROJECT_DIR"], "screencap")

    start_record()

    keyboard.wait("f6", suppress=True)
    stop_record()

    activate_cur_terminal()

    # Save file
    name = input("input file name (no ext): ")
    if not name:
        print2("Discard %s." % TEMP_FILE, color="red")
        os.remove(TEMP_FILE)

    else:
        dst_file = os.path.join(
            out_dir, "%d-%s.mp4" % (int(time.time()), slugify(name))
        )
        save_record(dst_file)
        print2("File saved: %s" % dst_file, color="green")

        call_echo(["mpv", dst_file])

    sleep(1)
