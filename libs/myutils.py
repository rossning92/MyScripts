import os
import sys
import subprocess
import json
import jinja2
import re
import tempfile
import yaml
import platform
import ctypes
from _shutil import run_elevated, conemu_wrap_args, append_line, update_env_var_explorer
from _script import *
import shlex


def msbuild(vcproj, build_config='Release'):
    print('[ Building `%s`... ]' % os.path.basename(vcproj))

    msbuild = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
    ]
    msbuild = [x for x in msbuild if os.path.exists(x)]
    assert len(msbuild) > 0

    params = '/p:Configuration=' + build_config + ' /p:WarningLevel=0 /p:Platform=x64 /maxcpucount /verbosity:Quiet /nologo'

    args = '"%s" %s "%s"' % (msbuild[0], params, vcproj)
    ret = subprocess.call(args)
    assert ret == 0
