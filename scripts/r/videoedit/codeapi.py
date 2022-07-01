import os

from _shutil import get_hash

from . import core, coreapi
from .uiautomate import record_ipython, record_wt_cmd, record_wt_node
from .uiautomate.record_alacritty import (
    open_alacritty,
    open_bash,
    open_cmd,
    record_term,
)
from .uiautomate.record_screen import record_app


@core.api
def codef(
    file,
    track="vid",
    size=None,
    jump_line=None,
    fontsize=None,
    mark_line=None,
    bg=None,
    **kwargs,
):
    from web.gen_code_image import gen_code_image_from_file

    os.makedirs("tmp/code", exist_ok=True)
    hash = get_hash(
        str((file, os.path.getmtime(file), size, jump_line, fontsize, mark_line, bg))
    )
    out_file = "tmp/code/%s.png" % hash
    if not os.path.exists(out_file):
        gen_code_image_from_file(
            file,
            out_file,
            size=size,
            jump_line=jump_line,
            fontsize=fontsize,
            mark_line=mark_line,
            bg=bg,
        )

    coreapi.add_video_clip(out_file, track=track, transparent=False, **kwargs)

    return out_file


@core.api
def ipython(cmd, file=None, startup=None, font_size=14, **kwargs):
    if file is None:
        file = "screencap/ipython/%s.mp4" % get_hash(cmd)
    if not os.path.exists(file) or core.force:
        record_ipython(file, cmd, startup=startup, font_size=font_size)
    return coreapi.clip(file, **kwargs)


@core.api
def cmd(cmd, font_size=14, file=None, **kwargs):
    if file is None:
        file = "screencap/cmd/%s.mp4" % get_hash(cmd)
    if not os.path.exists(file) or core.force:
        record_wt_cmd(file, cmd, font_size=font_size, **kwargs)
    return coreapi.clip(file, **kwargs)


@core.api
def node(cmd, font_size=14, file=None, sound=False, **kwargs):
    if file is None:
        file = "screencap/node/%s.mp4" % get_hash(cmd)
    if not os.path.exists(file) or core.force:
        record_wt_node(file, cmd, font_size=font_size, sound=sound)
    return coreapi.clip(file, **kwargs)


@core.api
def term(cmd=None, file=None, **kwargs):
    if file is None:
        file = "screencap/term/%s.mp4" % get_hash(cmd)
    if not os.path.exists(file) or core.force:
        record_term(file=file, cmd=cmd, **kwargs)
    return coreapi.clip(file, **kwargs)


@core.api
def bash(*args, **kwargs):
    term(*args, **kwargs)


@core.api
def screencap(*, file, args, title, size=(1920, 1080), uia_callback=None, **kwargs):
    if not os.path.exists(file) or core.force:
        record_app(
            args=args, file=file, size=size, uia_callback=uia_callback, title=title
        )
    return coreapi.clip(file, **kwargs)


core.api(open_alacritty, optional=True)
core.api(open_bash, optional=True)
core.api(open_cmd, optional=True)
