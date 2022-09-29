from _android import setup_android_env
from _shutil import call_echo

if __name__ == "__main__":
    setup_android_env()

    packages = [
        "ndk;21.4.7075529",
    ]

    for pkg in packages:
        call_echo(["sdkmanager", pkg])
