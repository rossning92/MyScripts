import os
import re
import runpy
import subprocess
import sys
from importlib import import_module
from importlib.abc import MetaPathFinder

PYTHON_MODULE_LIST = {
    "cv2": "opencv-python",
    "filelock": "filelock",  # a platform independent file lock.
    "flask": "Flask",
    "jieba": "jieba",
    "jinja2": "jinja2",
    "keyboard": "keyboard",
    "markdown2": "markdown2",
    "matplotlib": "matplotlib",
    "moviepy": "moviepy",
    "mss": "mss",
    "numpy": "numpy",
    "openai": "openai",
    "pandas": "pandas",
    "perfetto": "perfetto",
    "PIL": "pillow",
    "prompt_toolkit": "prompt_toolkit",  # Not compatible with PyInquirer
    "pyaudio": "pyaudio",
    "pyautogui": "pyautogui",
    "pyftpdlib": "pyftpdlib",
    "pyppeteer": "pyppeteer",
    "PyQt5": "PyQt5",
    "pyscreenshot": "pyscreenshot",
    "requests": "requests",
    "rich": "rich",
    "scipy": "scipy",
    "scrapy": "Scrapy",
    "selenium": "selenium",
    "simpleaudio": "simpleaudio",
    "skimage": "scikit-image",
    "slugify": "python-slugify",
    "websockets": "websockets",
    "win32api": "pywin32",
    "win32con": "pywin32",
    "win32gui": "pywin32",
    "win32ui": "pywin32",
    "yaml": "pyyaml",
}


class MyMetaPathFinder(MetaPathFinder):
    """
    A importlib.abc.MetaPathFinder to auto-install missing modules using pip
    """

    def find_spec(fullname, path, target=None):
        if path is None:
            if fullname in PYTHON_MODULE_LIST:
                installed = subprocess.call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--user",
                        PYTHON_MODULE_LIST[fullname],
                    ]
                )
                if installed == 0:
                    return import_module(fullname)


os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
sys.meta_path.append(MyMetaPathFinder)


if __name__ == "__main__":
    del sys.argv[0]

    module_file = sys.argv[0]
    module_dir = os.path.dirname(os.path.abspath(module_file))
    if os.path.exists(os.path.join(module_dir, "__init__.py")):
        # Goto parent folder
        os.chdir(os.path.dirname(module_dir))

        # Module name
        module_name = (
            os.path.basename(module_dir)
            + "."
            + re.sub("\\.py$", "", os.path.basename(module_file))
        )

        # Run module
        runpy.run_module(module_name, run_name="__main__")
        # subprocess.check_call([sys.executable, "-m", module_name] + sys.argv[1:])
    else:
        runpy.run_path(module_file, run_name="__main__")
