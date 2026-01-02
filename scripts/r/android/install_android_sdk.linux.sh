set -e

cd "$HOME"

# https://developer.android.com/studio#command-tools
if [[ ! -d ~/Android/Sdk ]]; then
    mkdir -p ~/Android/Sdk
    wget https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip -O commandlinetools.zip
    unzip commandlinetools.zip -d ~/Android/Sdk
    rm commandlinetools.zip
fi

export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$ANDROID_HOME/cmdline-tools/bin:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools:$PATH"

# https://developer.android.com/tools/sdkmanager
yes | sdkmanager --sdk_root="$ANDROID_HOME" --licenses
