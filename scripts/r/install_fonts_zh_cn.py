from _shutil import *


def install_font(url):
    make_and_change_dir(expanduser("~/Downloads"))
    download(url)
    unzip(os.path.basename(url))

    chdir(os.path.splitext(os.path.basename(url))[0])
    for f in glob.glob("*.otf"):
        font_name = os.path.splitext(f)[0]
        dst_file = os.path.join(
            expanduser("~\\AppData\\Local\\Microsoft\\Windows\\Fonts"),
            os.path.basename(f),
        )
        copy(f, dst_file)
        command = rf'reg add "HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "{font_name}" /t REG_SZ /d "{dst_file}" /f'
        call_echo(command)


install_font(
    "https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SourceHanSansSC.zip"
)

install_font(
    "https://raw.githubusercontent.com/adobe-fonts/source-han-serif/release/SubsetOTF/SourceHanSerifCN.zip"
)
