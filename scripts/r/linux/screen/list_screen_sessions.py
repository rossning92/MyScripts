import subprocess

from utils.menu import Menu


def select_screen_to_attach():
    try:
        out = subprocess.check_output(["screen", "-ls"], universal_newlines=True)
        lines = out.splitlines()
        print(lines)
        lines = [x.strip() for x in lines if x.startswith("\t")]
        m = Menu(items=lines)
        m.exec()
        selected = m.get_selected_item()
        if selected is not None:
            id = selected.split(".")[0]
            subprocess.call(["screen", "-d", "-r", id])
    except subprocess.CalledProcessError as e:
        print(e.output)


if __name__ == "__main__":
    select_screen_to_attach()
