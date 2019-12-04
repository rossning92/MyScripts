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

    setting_path = expandvars(r'%USERPROFILE%\Documents\ShareX')
    if not exists(setting_path):
        subprocess.Popen([exe_path, '-silent'], close_fds=True)
        while subprocess.call('tasklist | find "ShareX.exe"', shell=True) == 0:
            subprocess.call('taskkill /im ShareX.exe')
            time.sleep(0.5)

    config_file = os.path.join(setting_path, 'ApplicationConfig.json')
    config = json.load(open(config_file))
    config['DefaultTaskSettings']['UploadSettings']['NameFormatPattern'] = '%yy%mo%d%h%mi%s_%ms'
    config['DefaultTaskSettings']['UploadSettings']['NameFormatPatternActiveWindow'] = '%yy%mo%d%h%mi%s_%ms'
    # config['DefaultTaskSettings']['CaptureSettings']['FFmpegOptions']
    json.dump(config, open(config_file, 'w'))

    config_file = os.path.join(setting_path, 'HotkeysConfig.json')
    config = json.load(open(config_file))
    config['Hotkeys'][0]['HotkeyInfo']['Hotkey'] = 'F1'
    json.dump(config, open(config_file, 'w'))

    subprocess.call('taskkill /f /im ShareX.exe')
    subprocess.Popen([exe_path, '-silent'], close_fds=True)


# install_snipaste()
install_sharex()
