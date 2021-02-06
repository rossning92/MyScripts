from _shutil import *


def install_font(url):
    make_and_change_dir(expanduser("~/Downloads"))
    download(url)
    unzip(os.path.basename(url))

    chdir(os.path.splitext(os.path.basename(url))[0])
    for f in glob.glob("**/*.otf", recursive=True):
        font_file_name = os.path.basename(f)
        font_name = os.path.splitext(font_file_name)[0]
        dst_file = os.path.join(r"C:\Windows\Fonts", os.path.basename(f))
        copy(f, dst_file)
        command = rf'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "{font_name}" /t REG_SZ /d "{font_file_name}" /f'
        call_echo(command)


if __name__ == "__main__":
    install_font(
        "https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SourceHanSansSC.zip"
    )

    install_font(
        "https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SourceHanSerifSC_EL-M.zip"
    )
    install_font(
        "https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SourceHanSerifSC_SB-H.zip"
    )
