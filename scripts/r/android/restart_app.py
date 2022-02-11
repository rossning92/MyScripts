import argparse

from _android import logcat, restart_app
from _shutil import setup_logger

if __name__ == "__main__":
    setup_logger()
    # Run app using monkey:
    # adb shell monkey -p your.app.package.name -c android.intent.category.LAUNCHER 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg", default=None)
    args = parser.parse_args()

    if args.pkg is not None:
        pkg = args.pkg
    else:
        pkg = r"{{PKG_NAME}}"

    restart_app(pkg, use_monkey="{{USE_MONKEY}}")
    if "{{_SHOW_LOGCAT}}":
        logcat(proc_name=pkg)
