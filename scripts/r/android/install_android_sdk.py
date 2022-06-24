import subprocess

from _android import setup_android_env

if __name__ == "__main__":
    setup_android_env()

    packages = [
        "platform-tools",
        # 'platforms;android-24',
        # 'platforms;android-26',
        # "build-tools;27.0.3",
        # 'lldb;3.1',
        # "ndk;18.1.5063045",
        # 'ndk-bundle',
        # For UE4.25
        # (https://docs.unrealengine.com/en-US/Platforms/Mobile/Android/Setup/AndroidStudio/index.html)
        "platforms;android-28",
        "build-tools;28.0.3",
        # "lldb;3.1",
        # "cmake;3.10.2.4988404",
        # "ndk;21.1.6352462",
    ]

    for pkg in packages:
        subprocess.check_call(["sdkmanager", pkg], shell=True)
