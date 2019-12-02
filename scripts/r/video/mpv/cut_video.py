from _appmanager import *
from _shutil import *

mpv = get_executable('mpv')
file = get_files()[0]

subprocess.Popen(['mpv',
                  '--script=%s' % os.path.realpath(os.path.dirname(__file__)),
                  '--script-opts=osc-layout=bottombar',
                  file])
