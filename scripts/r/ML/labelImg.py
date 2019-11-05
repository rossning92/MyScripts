from _shutil import *

INSTALL_DIR = r'C:\tools\labelImg'

if not exists(INSTALL_DIR):
    cd(gettempdir())
    file = download('https://github.com/tzutalin/labelImg/files/2638199/windows_v1.8.1.zip')

    mkdir(INSTALL_DIR)
    unzip(file, to=INSTALL_DIR)

cd(INSTALL_DIR)
exe_file = glob.glob('**\\labelImg.exe', recursive=True)[0]
subprocess.Popen(exe_file, close_fds=True)
