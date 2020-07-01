from _shutil import *

INSTALL_PATH = os.path.expandvars(r"%LOCALAPPDATA%\carnac")


with open(r"C:\ProgramData\Carnac\PopupSettings.settings", "w") as f:
    f.write(
        r'[{"Key":"FontSize","Value":"60"},'  # 400
        r'{"Key":"ItemBackgroundColor","Value":"Maroon"},'
        r'{"Key":"FontColor","Value":"White"},'
        r'{"Key":"TopOffset","Value":"0"},'
        r'{"Key":"BottomOffset","Value":"100"},'
        r'{"Key":"LeftOffset","Value":"0"},'
        r'{"Key":"RightOffset","Value":"100"},'
        r'{"Key":"AutoUpdate","Value":"false"},'
        r'{"Key":"ItemMaxWidth","Value":"500"},'  # 350
        r'{"Key":"ItemOpacity","Value":"0.5"},'
        r'{"Key":"ItemFadeDelay","Value":"2"},'
        r'{"Key":"DetectShortcutsOnly","Value":"false"},'
        r'{"Key":"ShowOnlyModifiers","Value":"true"},'
        r'{"Key":"ShowSpaceAsUnicode","Value":"false"},'
        r'{"Key":"ShowApplicationIcon","Value":"false"},'
        r'{"Key":"ProcessFilterExpression","Value":""},'
        r'{"Key":"Screen","Value":"1"},'
        r'{"Key":"Placement","Value":"BottomRight"},'
        r'{"Key":"Left","Value":"0"},'
        r'{"Key":"SettingsConfigured","Value":"true"}]'
    )

subprocess.call("taskkill /f /im Carnac.exe")
subprocess.Popen(os.path.expandvars(r"%LOCALAPPDATA%\carnac\Carnac.exe"))
