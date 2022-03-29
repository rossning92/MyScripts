import os
import subprocess
import tempfile

from _shutil import call2, call_echo, print2


def ue4_command(cmd):
    # Engine/Build/Android/Java/src/com/epicgames/ue4/ConsoleCmdReceiver.java
    args = "adb shell \"am broadcast -a android.intent.action.RUN -e cmd '%s'\"" % cmd
    call_echo(args, no_output=True)


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


def update_config(ini_file, section, kvps):
    print("== " + ini_file + " ==")
    print(section)

    if os.path.exists(ini_file):
        with open(ini_file) as f:
            lines = f.readlines()
    else:
        lines = []

    lines = [line.rstrip() for line in lines]

    # Only updated modified kvps
    updated_kvps = []
    for kvp in kvps:
        if kvp in lines:
            print2("= %s" % kvp, color="black")
        else:
            updated_kvps.append(kvp)
            print2("+ %s" % kvp, color="green")

    # Remove existing value
    for kvp in updated_kvps:
        if not kvp:
            continue

        k, _ = kvp.split("=")
        indices = [i for i in range(len(lines)) if lines[i].startswith(k + "=")]
        lines = [lines[i] for i in range(len(lines)) if i not in indices]

    # Find section
    try:
        i = lines.index(section)
        i += 1

    except ValueError:
        lines.append("")
        lines.append(section)
        i = len(lines)

    # Add value
    lines[i:i] = updated_kvps

    # Save to file
    call2('attrib -r "%s"' % ini_file)
    os.makedirs(os.path.dirname(ini_file), exist_ok=True)
    with open(ini_file, "w") as f:
        f.write("\n".join(lines))

    print()
