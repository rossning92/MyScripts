import argparse
import os
import subprocess

from utils.menu import Menu
from utils.menu.logviewer import LogViewerMenu

log_filter_dir = os.path.join(os.environ["MY_DATA_DIR"], "log_filters")


class _FilterMenu(Menu[str]):
    def __init__(self):
        log_filters = (
            [
                os.path.splitext(f)[0]
                for f in os.listdir(log_filter_dir)
                if f.endswith(".txt")
            ]
            if os.path.isdir(log_filter_dir)
            else []
        )

        super().__init__(
            items=log_filters,
            prompt="/",
        )


class LogViewer(LogViewerMenu):
    def __init__(self, file: str) -> None:
        super().__init__(file=file)

        self.add_command(lambda: self.filter_logs(), hotkey="ctrl+f")

    def filter_logs(self):
        m = _FilterMenu()
        m.exec()
        filter_name = m.get_selected_item()
        if filter_name:
            with open(
                os.path.join(log_filter_dir, f"{filter_name}.txt"),
                "r",
                encoding="utf-8",
            ) as f:
                self.set_input(f.read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", default=None, type=str)
    parser.add_argument("--cmdline", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.cmdline:
        with open(args.file, "w") as f:
            ps = subprocess.Popen(args.cmdline, stdout=f, stderr=f)
            LogViewer(file=args.file).exec()
            ps.wait()

    else:
        LogViewer(file=args.file).exec()
