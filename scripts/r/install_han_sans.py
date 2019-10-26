from _shutil import *

make_and_change_dir(expanduser('~/Downloads'))
download('https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SourceHanSansSC.zip')
unzip('SourceHanSansSC.zip')

chdir('SourceHanSansSC')
copy('*.otf', expanduser('~/AppData/Local/Microsoft/Windows/Fonts/'))
for f in glob.glob('*.otf'):
    font_name = os.path.splitext(f)[0]
    full_path = os.path.realpath(f)
    command = rf'reg add "HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "{font_name}" /t REG_SZ /d "{full_path}" /f'
    call_echo(command)
