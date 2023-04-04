import os
import subprocess
import time
from tempfile import gettempdir

from _shutil import call_echo, get_cur_time_str, get_home_path

# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace


IMPORT_PATH = os.path.join(get_home_path(), "perfetto")


def start_trace(config_str, open_trace=True, detached_mode=False, out_file=None):
    subprocess.check_call(["adb", "root"])
    ps = subprocess.Popen(
        [
            r"protoc",
            "--encode=perfetto.protos.TraceConfig",
            "-I",
            IMPORT_PATH,
            "protos/perfetto/config/perfetto_config.proto",
        ],
        stdin=subprocess.PIPE,
        stdout=open(os.path.join(gettempdir(), "config.bin"), "wb"),
    )
    ps.stdin.write(config_str.encode())
    ps.stdin.close()
    ps.wait()

    call_echo(["adb", "shell", "killall perfetto"], check=False)
    call_echo(
        [
            "adb",
            "push",
            os.path.join(gettempdir(), "config.bin"),
            "/data/misc/perfetto-traces/config.bin",
        ],
        check=True,
    )

    if detached_mode:
        pid = subprocess.check_output(
            [
                "adb",
                "shell",
                "perfetto",
                "-c",
                "/data/misc/perfetto-traces/config.bin",
                "-o",
                "/data/misc/perfetto-traces/trace",
                "--background",
            ],
        )
        pid = int(pid)

        input("press enter to stop perfetto (PID=%d)..." % pid)
        call_echo(["adb", "shell", "kill -9 %d" % pid])
        time.sleep(5)

    else:
        call_echo(
            [
                "adb",
                "shell",
                "perfetto",
                "-c",
                "/data/misc/perfetto-traces/config.bin",
                "-o",
                "/data/misc/perfetto-traces/trace",
            ],
            check=True,
        )

    if out_file is None:
        out_file = os.path.join(
            get_home_path(), "Desktop", "trace-%s.perfetto-trace" % get_cur_time_str()
        )
    call_echo(["adb", "pull", "/data/misc/perfetto-traces/trace", out_file])

    if open_trace:
        subprocess.check_call(
            ["run_script", "r/android/perfetto/open_perfetto_trace.py", out_file]
        )

    return out_file
