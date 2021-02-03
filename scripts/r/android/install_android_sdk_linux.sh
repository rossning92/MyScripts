set -e

cd ~


# sudo apt update
# sudo apt install android-sdk -y
# sudo apt install unzip -y


# wget https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip
# unzip sdk-tools-linux-*.zip
# rm sdk-tools-linux-*.zip

cd ~/tools/bin

# ./sdkmanager --update
./sdkmanager "build-tools;27.0.3"
./sdkmanager "lldb;3.1"
./sdkmanager "ndk-bundle"
