from _shutil import *


def find_path(p):
    found = list(glob.glob(p))
    if len(found) != 1:
        raise Exception(f'Finding {p}: {str(found)}')
    return found[0]


def setup_nvpack(nvpack_root=None):
    if not nvpack_root:
        nvpack_root = 'C:\\NVPACK'

    NVPACK = {
        "ANDROID_HOME": nvpack_root + "\\android-sdk-windows",
        "ANDROID_NDK_ROOT": nvpack_root + "\\android-ndk-r12b",
        "ANT_HOME": nvpack_root + "\\apache-ant-1.8.2",
        "GRADLE_HOME": nvpack_root + "\\gradle-2.9",
        "JAVA_HOME": nvpack_root + "\\jdk1.8.0_77",
        "NDKROOT": nvpack_root + "\\android-ndk-r12b",
        "NDK_ROOT": nvpack_root + "\\android-ndk-r12b",
        "NVPACK_NDK_TOOL_VERSION": "4.9",
        "NVPACK_NDK_VERSION": "android-ndk-r12b",
        "NVPACK_ROOT": nvpack_root,
        "PATH": [
            # "C:\\NVPACK\\gradle-2.9\\bin",
            # "C:\\NVPACK\\apache-ant-1.8.2\\bin",
            # "C:\\NVPACK\\jdk1.8.0_77\\bin",
            # "C:\\NVPACK\\android-ndk-r12b",
            nvpack_root + "\\android-sdk-windows\\extras\\android\\support",
            nvpack_root + "\\android-sdk-windows\\build-tools",
            nvpack_root + "\\android-sdk-windows\\platform-tools",
            nvpack_root + "\\android-sdk-windows\\tools"
        ]
    }
    if exists(nvpack_root):
        print('NVPACK Found: ' + nvpack_root)

        # NDK
        ndk = find_path(nvpack_root + '\\android-ndk-*')
        NVPACK['ANDROID_NDK_ROOT'] = NVPACK['NDKROOT'] = NVPACK['NDK_ROOT'] = ndk
        NVPACK['PATH'].insert(0, ndk)

        # Java
        java = find_path(nvpack_root + '\\jdk*')
        NVPACK['JAVA_HOME'] = java
        NVPACK['PATH'].insert(0, java + '\\bin')

        # Ant
        ant = find_path(nvpack_root + '\\apache-ant-*')
        NVPACK['ANT_HOME'] = ant
        NVPACK['PATH'].insert(0, ant + '\\bin')

        # Gradle
        gradle = find_path(nvpack_root + '\\gradle-*')
        NVPACK['ANT_HOME'] = gradle
        NVPACK['PATH'].insert(0, gradle + '\\bin')

        print('Setup NVPACK env...')
        for k, v in NVPACK.items():
            if k != 'PATH':
                env[k] = v
            else:
                prepend_to_path(v)
