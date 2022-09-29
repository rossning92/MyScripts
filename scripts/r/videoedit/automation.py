import os

from _shutil import get_hash

from . import common
from .uiautomate import record_ipython, record_wt_cmd, record_wt_node
from .uiautomate.record_alacritty import open_alacritty, open_bash, open_cmd
from .uiautomate.record_alacritty import record_term as _record_term
from .uiautomate.record_alacritty import term
from .uiautomate.record_screen import record_app


# deprecated
@common.api
def ipython(cmd, file=None, startup=None, font_size=14, **kwargs):
    if file is None:
        file = "screencap/ipython/%s.mp4" % get_hash(cmd)
    if common.force or not os.path.exists(file):
        record_ipython(file, cmd, startup=startup, font_size=font_size)
    return file


# deprecated
@common.api
def cmd(cmd, font_size=14, file=None, **kwargs):
    if file is None:
        file = "screencap/cmd/%s.mp4" % get_hash(cmd)
    if common.force or not os.path.exists(file):
        record_wt_cmd(file, cmd, font_size=font_size, **kwargs)
    return file


# deprecated
@common.api
def node(cmd, font_size=14, file=None, sound=False, **kwargs):
    if file is None:
        file = "screencap/node/%s.mp4" % get_hash(cmd)
    if common.force or not os.path.exists(file):
        record_wt_node(file, cmd, font_size=font_size, sound=sound)
    return file


@common.api
def screencap(file, args=None, title=None, size=(1920, 1080), callback=None, **kwargs):
    if common.force or not os.path.exists(file):
        record_app(args=args, file=file, size=size, callback=callback, title=title)
    return file


@common.api
def record_term(cmd, file, **kwargs):
    if common.force or not os.path.exists(file):
        _record_term(cmd=cmd, file=file, **kwargs)
    return file


common.api(open_alacritty, skip=True)
common.api(open_bash, skip=True)
common.api(open_cmd, skip=True)
common.api(term, skip=True)
