#!/bin/bash

port=10000

set -e

adb root
adb disconnect

echo "Please connect the device to USB..."
adb wait-for-device

echo "Get IP address of wlan0..."
ip=$(adb shell "ifconfig wlan0" | grep -oP 'inet addr:\K\S+')
if [ -z "$ip" ]; then
    echo "Cannot find wlan IP address."
    exit 1
fi

echo "Start adb server in tcp mode..."
adb tcpip $port
adb wait-for-device

echo "Connect to $ip:$port over wifi..."
out=$(adb connect "$ip:$port" | tr -d '\r' | tr -d '\n')

echo "$out"
if [[ $out == *"failed"* ]]; then
    echo "$out"
    exit 1
fi

run_script ext/set_variable.py ANDROID_SERIAL "$ip:$port"
