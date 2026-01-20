from _shutil import call_echo, menu_item, menu_loop, print2, write_temp_file

call_echo("pip install --upgrade --pre uiautomator2")

import uiautomator2 as u2
from utils.android import setup_android_env
from utils.editor import open_code_editor


@menu_item(key="d")
def dump_ui_hierarchy():
    xml = d.dump_hierarchy()
    xml_file = write_temp_file(xml, ".xml")
    open_code_editor(xml_file)


@menu_item(key="w")
def weditor_viewer():
    call_echo("weditor")


@menu_item(key="R")
def reset(purge=True):
    global d
    if purge:
        call_echo("python -m uiautomator2 purge")
    call_echo("python -m uiautomator2 init")
    d = u2.connect()  # connect to device
    print(d.info)


if __name__ == "__main__":
    setup_android_env()

    reset(purge=False)

    while True:
        try:
            menu_loop()
        except Exception as ex:
            print2("ERROR: %s" % ex, color="red")

    # https://github.com/openatx/uiautomator2
    # python -m uiautomator2 init
    # "C:\Android\android-sdk\tools\bin\uiautomatorviewer.bat"
    # pip install --upgrade --pre uiautomator2
