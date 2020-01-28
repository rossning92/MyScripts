from _shutil import *

call2('vagrant upload hello hello {{VAGRANT_ID}}')
call2('vagrant ssh -c "cd ~/hello ; bash build.sh" {{VAGRANT_ID}}')
