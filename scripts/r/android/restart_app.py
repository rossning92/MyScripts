from _android import restart_app, logcat
import argparse

if __name__ == "__main__":
    # Run app using monkey:
    # adb shell monkey -p your.app.package.name -c android.intent.category.LAUNCHER 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg", default=None)
    args = parser.parse_args()

    if args.pkg is not None:
        pkg = args.pkg
    else:
        pkg = r"{{PKG_NAME}}"

    restart_app(pkg, use_monkey=False)
    if "{{_SHOW_LOGCAT}}":
        logcat(proc_name=pkg)
