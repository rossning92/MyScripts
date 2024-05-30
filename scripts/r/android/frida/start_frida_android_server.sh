# https://frida.re/docs/android/

set -e

# Install Frida’s CLI tools: https://frida.re/docs/installation/
pip install frida-tools

cd /tmp

if [[ ! -f 'frida-server' ]]; then
    url='https://github.com/frida/frida/releases/download/16.1.3/frida-server-16.1.3-android-arm64.xz'
    curl -O -L "$url"
    xz -d -c frida-server-16.1.3-android-arm64.xz >frida-server
fi

adb root

if ! adb shell test -f "/data/local/tmp/frida-server"; then
    # Push frida-server
    adb push frida-server /data/local/tmp/
    adb shell "chmod 755 /data/local/tmp/frida-server"
fi

adb shell 'kill $(pidof frida-server)' || true
adb shell "nohup /data/local/tmp/frida-server &> /dev/null &"
