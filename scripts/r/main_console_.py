import sys
import os

sys.path.append(os.path.realpath("../../libs"))
sys.path.append(os.path.realpath("../../bin"))

import run_python
from _script import *
from prompt_toolkit import prompt
from prompt_toolkit.completion import (
    WordCompleter,
    FuzzyWordCompleter,
    FuzzyCompleter,
    Completer,
    Completion,
)


scripts = []
modified_time = {}

load_scripts(scripts, modified_time, autorun=False)


class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        for i, script in enumerate(scripts):
            yield Completion(script.name)


while True:
    text = prompt(
        "> ",
        completer=FuzzyWordCompleter([x.name for x in scripts],),
        complete_while_typing=True,
    )
    found = list(filter(lambda x: x.name == text, scripts))
    if found:
        list(found)[0].execute()
    else:
        print2("ERROR: unrecognized command.", color="red")
