import argparse
import os
import subprocess

from utils.menu.filemenu import FileMenu
from utils.menu.jsoneditmenu import JsonEditMenu


class CallGraphMenu(JsonEditMenu):
    def __init__(self, config_file: str):
        self.__config_file = config_file

        super().__init__(
            json_file=config_file,
            default={
                "root": os.getcwd(),
                "files": [],
                "match": "",
                "match_callers": 2,
                "match_callees": 1,
            },
            save_modified_only=False,
        )

        self.add_command(self.__generate_callgraph, hotkey="alt+e")

    def __generate_callgraph(self):
        self.call_func_without_curses(
            lambda: subprocess.check_call(
                ["run_script", "r/dev/gen_callgraph.py", "-C", self.__config_file]
            )
        )


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str, nargs="?")
    args = parser.parse_args()

    if not args.config_file:
        callgraph_dir = os.path.join(os.path.expanduser("~"), "callgraph")
        os.makedirs(callgraph_dir, exist_ok=True)
        menu = FileMenu(
            prompt="select callgraph config",
            goto=callgraph_dir,
            show_size=False,
            recursive=True,
            allow_cd=False,
        )
        menu.select_file()
        file_name = menu.get_input()
        if file_name:
            config_file = os.path.join(callgraph_dir, file_name)
        else:
            return
    else:
        config_file = args.config_file
    CallGraphMenu(config_file=config_file).exec()


if __name__ == "__main__":
    _main()
