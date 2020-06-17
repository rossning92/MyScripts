from _shutil import *

cd("~/Projects")
call_echo("git clone https://github.com/Microsoft/vcpkg.git")
call_echo("bootstrap-vcpkg")
