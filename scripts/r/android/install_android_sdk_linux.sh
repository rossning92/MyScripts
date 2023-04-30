# https://developer.android.com/tools/sdkmanager

set -e
export use_proxy=yes
export http_proxy=192.168.42.240:8080
export https_proxy=192.168.42.240:8080

cd ~
# sudo apt install android-sdk -y

# Only install `unzip` if it isn't already installed
if ! command -v unzip >/dev/null; then
    sudo apt update
    sudo apt install unzip -y
else
    echo "unzip package is already installed"
fi

if [[ ! -d android-sdk ]]; then
    # wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
    mkdir -p android-sdk
    unzip commandlinetools-linux-9477386_latest.zip -d android-sdk
fi

export ANDROID_HOME=$HOME/android-sdk
export PATH="$ANDROID_HOME/cmdline-tools/bin:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools:$PATH"

sdkmanager --sdk_root=${ANDROID_HOME} "build-tools;28.0.3" "platform-tools" "platforms;android-28" "tools"
# ./sdkmanager "lldb;3.1"
# ./sdkmanager "ndk-bundle"
