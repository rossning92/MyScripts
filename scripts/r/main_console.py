from _script import *
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter, Completer, Completion


scripts = []
modified_time = {}

load_scripts(scripts, modified_time)


class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        for i, script in enumerate(scripts):
            yield Completion(script.name)


text = prompt('> ', completer=FuzzyCompleter(MyCustomCompleter()),
              complete_while_typing=True)
found = filter(lambda x: x.name == text, scripts)
if found:
    list(found)[0].execute()
