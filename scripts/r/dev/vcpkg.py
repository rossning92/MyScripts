import os

from _shutil import call_echo, menu_item, menu_loop

VCPKG_ROOT = os.path.join(os.path.expanduser("~"), "vcpkg")


@menu_item(key="s")
def search():
    kw = input("search for libaries: ")
    call_echo("vcpkg search %s" % kw)


def install_packages(x64=True):
    pkg_names = input("install by package name: ")
    for pkg in pkg_names.split(" "):
        call_echo("vcpkg install %s%s --recurse" % (pkg, ":x64-windows" if x64 else ""))


@menu_item(key="i")
def install_x64_windows():
    install_packages(x64=True)


@menu_item(key="I")
def install_x86_windows():
    install_packages(x64=False)


if __name__ == "__main__":
    if not os.path.exists(VCPKG_ROOT):
        call_echo(
            "git clone https://github.com/microsoft/vcpkg", os.path.dirname(VCPKG_ROOT)
        )
        call_echo(r".\vcpkg\bootstrap-vcpkg.bat", os.path.dirname(VCPKG_ROOT))

    os.chdir(VCPKG_ROOT)

    menu_loop()
