if ! [ -x "$(command -v avrdude)" ]; then
    sudo apt-get update
    sudo apt-get install avrdude -y
fi

avrdude -p m2560 -c wiring -P /dev/ttyUSB1 -b 115200 -U flash:w:CR-10S-300.hex
