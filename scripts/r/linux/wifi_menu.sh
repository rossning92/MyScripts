#!/usr/bin/env bash

while true; do
    stations=$(nmcli --fields "SSID,SECURITY" device wifi list | sed '/^--/d')
    choice=$(echo -e "Scan
Enable Wi-Fi
Disable Wi-Fi
Enter SSID
---
$stations" | fzf)
    ssid=$(echo "$choice" | sed 's/\s\{2,\}/\|/g' | awk -F "|" '{print $1}')

    if [ "$choice" = "Scan" ]; then
        nmcli dev wifi rescan
    else
        if [ "$choice" = "Disable Wi-Fi" ]; then
            nmcli radio wifi on
        elif [ "$choice" = "Enable Wi-Fi" ]; then
            nmcli radio wifi off
        else
            if [ "$choice" = "Enter SSID" ]; then
                read -p "SSID: " ssid
            fi

            # Check if the SSID is already saved.
            if echo "$(nmcli connection show)" | grep -q "$ssid"; then
                nmcli con up "$ssid"
            else
                if [[ "$choice" =~ "WPA2" ]] || [[ "$choice" =~ "WEP" ]]; then
                    read -p "Password: " pwd
                fi
                nmcli dev wifi con "$ssid" password "$pwd"
            fi
        fi
        exit 0
    fi
done
