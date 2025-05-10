import argparse
import os
import subprocess

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
    parser.add_argument("config_file")
    args = parser.parse_args()

    CallGraphMenu(config_file=args.config_file).exec()


if __name__ == "__main__":
    _main()
