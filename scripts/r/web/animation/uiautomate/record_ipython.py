from _shutil import call_echo

from ipython import open_wt_ipython
from uiautomate import *


def record_ipython(file, func, startup=None):
    if os.path.exists(file):
        return file

    else:
        return _record_ipython(file, func, startup=startup)


def _record_ipython(file, func, startup=None):
    call_echo(["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US'"])

    open_wt_ipython(startup=startup)

    recorder.rect = (0, 0, 1920, 1080)
    recorder.file = file

    recorder.start_record()

    func()

    sleep(2)
    recorder.stop_record()

    send_hotkey("alt", "f4")
    sleep(1)

    call_echo(
        ["powershell", "-command", "Set-WinUserLanguageList -Force 'zh-CN', 'en-US'"]
    )

    return file


if __name__ == "__main__":
    file = get_files()[0]
    out_file = os.path.splitext(file)[0] + ".mp4"

    action_list = []
    with open(file, encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in lines:
        match = re.match(r"^\{\{(.*?)}}$", line)
        if match:
            code = match.group(1)
            action_list.append(lambda code=code: exec(code, globals()))
        else:
            action_list.append(lambda line=line: typing(line + "\n"))

    def run_actions():
        for act in action_list:
            act()

    _record_ipython(out_file, run_actions, startup="import torch")
