from _shutil import *
from _term import *
import keyboard

out_dir = os.path.join(os.environ["VIDEO_PROJECT_DIR"], "screencap")
# out_dir = "/tmp"

tmp_file = os.path.join(gettempdir(), "screen-record.mp4")
ps = subprocess.Popen(
    [
        "captura-cli",
        "start",
        "--source",
        "222,150,1920,1080",
        "-r",
        "60",
        "--vq",
        "100",
        "-f",
        tmp_file,
        "-y",
    ],
    stdin=subprocess.PIPE,
)

keyboard.wait("f6", suppress=True)
ps.stdin.write(b"q")
ps.stdin.close()

activate_cur_terminal()

# Save file
name = input("input file name (no ext): ")
if not name:
    print2("Discard %s." % tmp_file, color="red")
    os.remove(tmp_file)

else:
    dst_file = os.path.join(out_dir, "%d-%s.mp4" % (int(time.time()), slugify(name)))
    os.makedirs(out_dir, exist_ok=True)
    os.rename(tmp_file, dst_file)
    print2("File saved: %s" % dst_file, color="green")

    call_echo(["mpv", dst_file])

sleep(1)
