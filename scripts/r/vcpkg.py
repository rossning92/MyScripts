from _shutil import *

cd("~/Projects")
if not os.path.exists("vcpkg"):
    call_echo("git clone https://github.com/Microsoft/vcpkg.git")

cd("vcpkg")

if not exists("vcpkg.exe"):
    call_echo("bootstrap-vcpkg")
    call_echo("vcpkg integrate install")

call_echo("vcpkg install glog gflags glfw3 glew glm ZLIB")
