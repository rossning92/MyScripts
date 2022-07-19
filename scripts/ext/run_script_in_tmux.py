import os

from _script import Script
from _shutil import convert_to_unix_path, exec_ahk, exec_bash, write_temp_file

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"]

    script = Script(script_path)
    s = script.render() + "\n"
    tmp_script_file = write_temp_file(s, ".sh")
    tmp_script_file = convert_to_unix_path(tmp_script_file, wsl=True)

    # exec_bash('tmux respawn-pane -k -t {left} "bash %s"' % tmp_script_file, wsl=True)
    exec_bash(
        'tmux split-window "bash %s"; tmux select-pane -t {previous}' % tmp_script_file,
        wsl=True,
    )

    exec_ahk("WinActivate r/linux/tmux")
