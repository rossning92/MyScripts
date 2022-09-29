export DESKTOP_SESSION=ubuntu
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
export GDMSESSION=ubuntu
export LIBGL_ALWAYS_INDIRECT=1
export XDG_CURRENT_DESKTOP=ubuntu:GNOME
export XDG_RUNTIME_DIR=~/xdg
export XDG_SESSION_CLASS="user"
export XDG_SESSION_DESKTOP=ubuntu
export XDG_SESSION_TYPE="x11"

"/mnt/c/Program Files/VcXsrv/vcxsrv.exe" -ac &

gnome-session --debug --disable-acceleration-check
