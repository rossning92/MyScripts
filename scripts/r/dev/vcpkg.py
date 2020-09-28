from _shutil import *

cd("~")
if not exists("vcpkg"):
    call_echo("git clone https://github.com/microsoft/vcpkg")
    call_echo(r".\vcpkg\bootstrap-vcpkg.bat")
    # cd("vcpkg")

while True:
    print("s - search\n" "q - quit\n" "i - install\n")
    ch = getch()
    if ch == "s":
        kw = input("search for libaries: ")
        call_echo(r".\vcpkg\vcpkg search %s" % kw)

    elif ch == "q":
        sys.exit(0)

    elif ch == "i":
        pkg_name = input("install by package name: ")
        call_echo(r".\vcpkg\vcpkg install %s --recurse" % pkg_name)

