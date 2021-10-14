cd ~
curl -OL https://dl.google.com/android/repository/platform-tools_r31.0.2-linux.zip
unzip platform-tools_r31.0.2-linux.zip

sudo ln -s ${HOME}/platform-tools/adb /usr/bin/adb
