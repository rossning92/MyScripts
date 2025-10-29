import io
import os
import subprocess
import sys
import urllib.request
import zipfile

_FONT_URL = "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansSC.zip"


def _register_font(font_name: str, dst_file: str):
    subprocess.check_output(
        [
            "reg",
            "add",
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
            "/v",
            font_name,
            "/t",
            "REG_SZ",
            "/d",
            dst_file,
            "/f",
        ],
        shell=True,
    )


def install_font():
    if sys.platform == "win32":
        dst_dir = r"C:\Windows\Fonts"
    elif sys.platform == "linux":
        dst_dir = os.path.expanduser("~/.local/share/fonts")
        os.makedirs(dst_dir, exist_ok=True)
    else:
        raise NotImplementedError("Unsupported OS: %s" % sys.platform)

    with urllib.request.urlopen(_FONT_URL) as response:
        data = response.read()

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".otf"):
                continue

            font_name = os.path.splitext(os.path.basename(name))[0]
            dst_file = os.path.join(dst_dir, os.path.basename(name))

            with open(dst_file, "wb") as fh:
                fh.write(zf.read(name))

            if sys.platform == "win32":
                _register_font(font_name, dst_file)


def get_font_file() -> str:
    font_candidates = [
        r"C:\Windows\Fonts\SourceHanSansSC-Bold.otf",
        os.path.expanduser("~/.local/share/fonts/SourceHanSansSC-Bold.otf"),
    ]
    font_file = next((path for path in font_candidates if os.path.exists(path)), None)
    if font_file is None:
        install_font()
        font_file = next(
            (path for path in font_candidates if os.path.exists(path)), None
        )
        if font_file is None:
            raise FileNotFoundError(
                "Source Han Sans SC Bold font not found after installation"
            )
    return font_file


if __name__ == "__main__":
    install_font()
