from _shutil import *
from _android import *

setup_android_env()

uproject_dir = r"{{UE4_PROJECT_DIR}}"
cd(uproject_dir)

uproject_file = glob.glob(os.path.join(uproject_dir, "*.uproject"))[0]
print(uproject_file)

call_echo(
    [
        r"{{UE_SOURCE}}\Engine\Build\BatchFiles\RunUAT.bat",
        "BuildCookRun",
        "-nocompileeditor",
        "-nop4",
        "-project=%s" % uproject_file,
        "-cook",
        "-stage",
        "-archive",
        "-archivedirectory=C:/tmp",
        "-package",
        # "-ue4exe=C:\Users\rossning92\Unreal Projects\UE4.25-OVR\Engine\Binaries\Win64\UE4Editor-Cmd.exe",
        "-pak",
        "-prereqs",  # Prerequisites installer
        "-nodebuginfo",
        "-targetplatform=Android",
        "-cookflavor=ASTC",
        "-build",
        "-CrashReporter",
        "-clientconfig=Shipping",
        "-utf8output",
        "-compile",
    ]
)


# taskkill /f /im {{UE4_PROJECT_NAME}}* 2>nul

# set BUILD_CONFIG=Development
# :: set BUILD_CONFIG=Debug


# call ..\_msbuild.cmd "{{UE_SOURCE}}\UE4.sln" /t:Games\{{UE4_PROJECT_NAME}} /p:Configuration="%BUILD_CONFIG%" /p:Platform=Win64 /maxcpucount /nologo
# if %errorlevel% neq 0 exit /b %errorlevel%


# exit /b 0


# :: call "{{UE_SOURCE}}\Engine\Build\BatchFiles\Build.bat" "{{UE4_PROJECT_NAME}}" Win64 %BUILD_CONFIG% -waitmutex-2017
