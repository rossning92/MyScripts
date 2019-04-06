from _shutil import *

NVPACK = {
    "ANDROID_HOME": "C:\\NVPACK\\android-sdk-windows",
    "ANDROID_NDK_ROOT": "C:\\NVPACK\\android-ndk-r12b",
    "ANT_HOME": "C:\\NVPACK\\apache-ant-1.8.2",
    "GRADLE_HOME": "C:\\NVPACK\\gradle-2.9",
    "JAVA_HOME": "C:\\NVPACK\\jdk1.8.0_77",
    "NDKROOT": "C:\\NVPACK\\android-ndk-r12b",
    "NDK_ROOT": "C:\\NVPACK\\android-ndk-r12b",
    "NVPACK_NDK_TOOL_VERSION": "4.9",
    "NVPACK_NDK_VERSION": "android-ndk-r12b",
    "NVPACK_ROOT": "C:\\NVPACK",
    "PATH": [
        "C:\\NVPACK\\gradle-2.9\\bin",
        "C:\\NVPACK\\apache-ant-1.8.2\\bin",
        "C:\\NVPACK\\jdk1.8.0_77\\bin",
        "C:\\NVPACK\\android-ndk-r12b",
        "C:\\NVPACK\\android-sdk-windows\\extras\\android\\support",
        "C:\\NVPACK\\android-sdk-windows\\build-tools",
        "C:\\NVPACK\\android-sdk-windows\\platform-tools",
        "C:\\NVPACK\\android-sdk-windows\\tools"
    ]
}

os.environ['DATA_CACHE_DIR'] = r'C:\UE4-DataCache'

chdir(r'{{UE_SOURCE}}\Engine\Binaries\Win64')

if exists('C:\\NVPACK'):
    print('Setup NVPACK env...')
    for k, v in NVPACK.items():
        if k != 'PATH':
            env[k] = v
        else:
            prepend_to_path(v)

# set UE-SharedDataCachePath=%DATA_CACHE_DIR%
# start UE4Editor.exe -ddc=noshared
Popen('UE4Editor.exe')
