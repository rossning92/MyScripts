# encoding: utf-8
from IPython.terminal.prompts import Prompts, Token
import os


class MyPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Other, u">>> "),
        ]

    def out_prompt_tokens(self):
        return [
            (Token.Prompt, ""),
        ]


ip = get_ipython()
ip.prompts = MyPrompts(ip)

from IPython.terminal import interactiveshell
from pygments.token import Token


import numpy as np

os.system("cls")
