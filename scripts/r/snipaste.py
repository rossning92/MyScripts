from _shutil import *
import zipfile


def unzip(file, to):
    mkdir(to)
    with zipfile.ZipFile(file, 'r') as zip:
        zip.extractall(to)


url = 'https://bbuseruploads.s3.amazonaws.com/472a0ba3-a3dd-4b9b-8eea-08bd5fa94e55/downloads/b3aac518-e6cc-4d0c-b52c-bd3ff1eb80f3/Snipaste-1.16.2-x64.zip?Signature=LfG7EuAO0qRcAF%2FO2JfE%2FNA6ax0%3D&Expires=1552281570&AWSAccessKeyId=AKIAIQWXW6WLXMB5QZAQ&versionId=8Q9.I.ovbR0tUaxGCNNKgbDKvmUzS6yx&response-content-disposition=attachment%3B%20filename%3D%22Snipaste-1.16.2-x64.zip%22'
install_dir = 'C:\\Snipaste'

if not exists(install_dir):
    chdir(gettempdir())
    download(url, 'Snipaste.zip')
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
