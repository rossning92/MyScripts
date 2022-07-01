import os

from _shutil import shell_open, write_temp_file

from .windows_terminal import record_windows_terminal

root = os.path.dirname(os.path.abspath(__file__))


def record_wt_node(file, cmd, font_size=14, sound=False):
    args = ["node", os.path.join(root, "_node_repl.js")]

    return record_windows_terminal(
        file,
        args=args,
        cmd=cmd,
        title="ross@ross-desktop2: node",
        font_size=font_size,
        icon=(root + "/icons/node.ico").replace("\\", "/"),
        sound=sound,
    )


if __name__ == "__main__":
    file = os.path.expanduser("~/Desktop/test.mp4")
    record_wt_node(file, "[] + \\{\\}{sleep 1}\n2 + 2\n")
    shell_open(file)
