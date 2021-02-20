from _shutil import *


def ue4_command(cmd):
    args = "adb shell \"am broadcast -a android.intent.action.RUN -e cmd '%s'\"" % cmd
    call_echo(args)


def ue4_recenter():
    ue4_command("vr.HeadTracking.Reset")


def ue4_show_stat():
    ue4_command("stat unit")
    ue4_command("stat fps")


def ue4_write_console_variables(ue4_project, pairs):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ini") as temp:
        temp_file_name = temp.name
        s = "[ConsoleVariables]\n" + "\n".join(pairs)
        temp.write(s.encode())

    subprocess.check_output(
        [
            "adb",
            "push",
            temp_file_name,
            "/sdcard/UE4Game/%s/%s/Saved/Config/Android/Engine.ini"
            % (ue4_project, ue4_project),
        ]
    )