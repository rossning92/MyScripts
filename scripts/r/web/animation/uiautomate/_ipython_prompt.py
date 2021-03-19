# encoding: utf-8
from IPython.terminal.prompts import Prompts, Token
import os
import numpy as np
from PIL import Image, ImageShow


class MyPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Other, ">>> "),
        ]

    def out_prompt_tokens(self):
        return [
            (Token.Prompt, ""),
        ]


class MyViewer(ImageShow.Viewer):
    format = "png"

    def get_command(self, file, **options):
        w = 1920 // 2
        h = w * 3 // 4
        left = (1920 - w) // 2
        top = (1080 - h) // 2

        return rf'mpv --no-terminal --geometry={w}x{h}+{left}+{top} "{file}"'


ImageShow.register(MyViewer, order=-1)

ip = get_ipython()
ip.prompts = MyPrompts(ip)

os.system("cls")
