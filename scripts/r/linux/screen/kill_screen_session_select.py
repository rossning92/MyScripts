import subprocess

from _screenutils import select_screen

if __name__ == "__main__":
    id = select_screen()
    if id:
        subprocess.call(["screen", "-XS", id, "quit"])
