# encoding: utf-8
from IPython.terminal.prompts import Prompts, Token
import os


class MyPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Prompt, u">>> "),
        ]

    def out_prompt_tokens(self):
        return [
            (Token.Prompt, ""),
        ]


ip = get_ipython()
# if getattr(ip, 'pt_cli', None):
ip.prompts = MyPrompts(ip)

import numpy as np

os.system("cls")
