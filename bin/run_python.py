import runpy
import sys
import subprocess
from importlib import import_module
from importlib.abc import MetaPathFinder


PYTHON_MODULE_LIST = {
    "jinja2": "jinja2",
    "keyboard": "keyboard",
    "markdown2": "markdown2",
    "matplotlib": "matplotlib",
    "scipy": "scipy",
    "numpy": "numpy",
    "pandas": "pandas",
    "PIL": "pillow",
    "pyftpdlib": "pyftpdlib",
    "pyppeteer": "pyppeteer",
    "PyQt5": "PyQt5==5.10.1",
    "yaml": "pyyaml",
    "requests": "requests",
    "slugify": "python-slugify",
    "win32api": "pywin32",
    "win32con": "pywin32",
    "win32gui": "pywin32",
    "win32ui": "pywin32",
    "websockets": "websockets",
    "filelock": "filelock",  # a platform independent file lock.
    "prompt_toolkit": "prompt_toolkit",  # Not compatible with PyInquirer
    "pyscreenshot": "pyscreenshot",
    "jieba": "jieba",
    "pyaudio": "pyaudio",
    "cv2": "opencv-python",
    "mss": "mss",
}


class MyMetaPathFinder(MetaPathFinder):
    """
    A importlib.abc.MetaPathFinder to auto-install missing modules using pip
    """

    def find_spec(fullname, path, target=None):
        if path == None:
            if fullname in PYTHON_MODULE_LIST:
                installed = subprocess.call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        PYTHON_MODULE_LIST[fullname],
                    ]
                )
                if installed == 0:
                    return import_module(fullname)


sys.meta_path.append(MyMetaPathFinder)

if __name__ == "__main__":
    del sys.argv[0]
    runpy.run_path(sys.argv[0], run_name="__main__")
