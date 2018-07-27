import subprocess
import os
import json


def msbuild(vcproj):
    print('[ Building `%s`... ]' % os.path.basename(vcproj))
    MSBUILD = r'"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe" /p:Configuration=Release /p:WarningLevel=0 /p:Platform=x64 /maxcpucount /verbosity:Quiet /nologo'
    
    args = '%s "%s"' % (MSBUILD, vcproj)
    ret = subprocess.call(args)
    assert ret == 0

def get_arg(name):
    path = os.path.join(os.path.dirname(__file__), '../variables.json')
    with open(path) as f:
        variables = json.load(f)
    return variables[name]