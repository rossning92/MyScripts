from _shutil import *

if platform.system() != 'Windows':
    sys.exit(0)


def install_snipaste():
    url = 'https://dl.snipaste.com/win-x64'
    install_dir = 'C:\\Snipaste'

    if not exists(install_dir):
        chdir(gettempdir())
        download(url, 'Snipaste.zip', redownload=True)
        unzip('Snipaste.zip', install_dir)

    with open(install_dir + '\\config.ini', 'w') as f:
        f.write('''[General]
language=en
startup_fix=true
first_run=false

[Hotkey]
delayed_snip=
snip="16777264, 112"
paste=
hide=
switch=
snip_and_copy=

[Snip]
ask_for_confirm_on_esc=false

[Update]
check_on_start=false
''')

    call(f'start {install_dir}\\Snipaste.exe')


def install_sharex():
    exe_path = r'C:\Program Files\ShareX\ShareX.exe'
    if not exists(exe_path):
        run_elevated('choco install sharex -y')

    subprocess.Popen(exe_path, close_fds=True)

    setting_path = expandvars(r'%USERPROFILE%\Documents\ShareX')


install_snipaste()
# install_sharex()
