from _shutil import *
from utils.android import *


def find_path(p):
    found = list(glob.glob(p))
    if len(found) != 1:
        raise Exception(f"Finding {p}: {str(found)}")
    return found[0]


def hack_replace_platform_tools(nvpack_root):
    adk_platform_tools = os.path.realpath(get_adk_path() + "/platform-tools")
    assert os.path.exists(adk_platform_tools)
    print2("ADB version:")
    call2([os.path.realpath(adk_platform_tools + "/adb.exe"), "--version"])

    nvpack_platform_tools = os.path.realpath(
        nvpack_root + "/android-sdk-windows/platform-tools"
    )
    assert os.path.exists(adk_platform_tools)

    if not os.path.exists(nvpack_platform_tools + "_bak"):
        os.rename(nvpack_platform_tools, nvpack_platform_tools + "_bak")
        call2('mklink /D "%s" "%s"' % (nvpack_platform_tools, adk_platform_tools))


def setup_nvpack(nvpack_root=None):
    if not nvpack_root:
        nvpack_root = "C:\\NVPACK"

    hack_replace_platform_tools(nvpack_root)

    NVPACK = {
        "ANDROID_HOME": nvpack_root + "\\android-sdk-windows",
        "NVPACK_NDK_TOOL_VERSION": "4.9",
        "NVPACK_NDK_VERSION": "android-ndk-r12b",
        "NVPACK_ROOT": nvpack_root,
        "PATH": [
            nvpack_root + "\\android-sdk-windows\\extras\\android\\support",
            nvpack_root + "\\android-sdk-windows\\build-tools",
            nvpack_root + "\\android-sdk-windows\\platform-tools",
            nvpack_root + "\\android-sdk-windows\\tools",
        ],
    }
    if exists(nvpack_root):
        print("NVPACK Found: " + nvpack_root)

        # NDK
        ndk = find_path(nvpack_root + "\\android-ndk-*")
        NVPACK["ANDROID_NDK_ROOT"] = NVPACK["NDKROOT"] = NVPACK["NDK_ROOT"] = ndk
        NVPACK["PATH"].insert(0, ndk)

        # Java
        java = find_path(nvpack_root + "\\jdk*")
        NVPACK["JAVA_HOME"] = java
        NVPACK["PATH"].insert(0, java + "\\bin")

        # Ant
        ant = find_path(nvpack_root + "\\apache-ant-*")
        NVPACK["ANT_HOME"] = ant
        NVPACK["PATH"].insert(0, ant + "\\bin")

        # Gradle
        gradle = find_path(nvpack_root + "\\gradle-*")
        NVPACK["ANT_HOME"] = gradle
        NVPACK["PATH"].insert(0, gradle + "\\bin")

        print("Setup NVPACK env...")
        for k, v in NVPACK.items():
            if k != "PATH":
                env[k] = v
            else:
                prepend_to_path(v)
