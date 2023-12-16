set -e

cd "$HOME"

# https://developer.android.com/studio#command-tools
if [[ ! -d ~/Android/Sdk ]]; then
    wget https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip -O commandlinetools.zip
    unzip commandlinetools.zip -d ~/Android/Sdk
    rm commandlinetools.zip
fi

export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$ANDROID_HOME/cmdline-tools/bin:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools:$PATH"

# https://developer.android.com/tools/sdkmanager
sdkmanager --sdk_root="${ANDROID_HOME}" --licenses
sdkmanager --sdk_root="${ANDROID_HOME}" "platform-tools" "platforms;android-33" "tools" "ndk-bundle"
