import os

from _shutil import get_hash

import core
import coreapi
from videoedit.uiautomate.ipython import record_ipython
from videoedit.uiautomate.wt_cmd import record_wt_cmd
from videoedit.uiautomate.wt_node import record_wt_node


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
def ipython(s, startup=None, font_size=14, **kwargs):
    out_file = "ipython/%s.mp4" % get_hash(s)
    if not os.path.exists(out_file):
        record_ipython(out_file, s, startup=startup, font_size=font_size)
    return coreapi.clip(out_file, **kwargs)


@core.api
def cmd(s, font_size=14, force=False, file=None, **kwargs):
    if file is None:
        file = "wt_cmd/%s.mp4" % get_hash(s)
    if not os.path.exists(file) or force:
        record_wt_cmd(file, s, font_size=font_size, **kwargs)
    return coreapi.clip(file, **kwargs)


@core.api
def node(s, font_size=14, force=False, file=None, sound=False, **kwargs):
    if file is None:
        file = "wt_node/%s.mp4" % get_hash(s)
    if not os.path.exists(file) or force:
        record_wt_node(file, s, font_size=font_size, sound=sound)
    return coreapi.clip(file, **kwargs)
