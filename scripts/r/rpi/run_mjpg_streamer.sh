set -e

killall -9 mjpg_streamer || true

if [ ! -d "mjpg-streamer-master" ]; then
    wget https://github.com/jacksonliam/mjpg-streamer/archive/master.zip -O mjpg-streamer.zip
    unzip mjpg-streamer.zip
    rm mjpg-streamer.zip
fi

cd mjpg-streamer-master/mjpg-streamer-experimental

if [ ! -f "input_uvc.so" ]; then
    sudo apt-get update
    sudo apt-get install cmake libjpeg9-dev -y
    sudo apt-get install gcc g++ -y
    make
    sudo make install
fi

# mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x480" -o "output_http.so -w ./www" &

# ip_addr=$(hostname -I | cut -d' ' -f1)
# echo "http://${ip_addr}:8080/?action=stream"

sudo tee /etc/systemd/system/mjpg_streamer.service <<-EOF
[Unit]
Description=A server for streaming Motion-JPEG from a video capture device
After=network.target

[Service]
ExecStart=/usr/local/bin/mjpg_streamer -i 'input_uvc.so -d /dev/video0 -r 640x480' -o 'output_http.so -w /usr/share/mjpg_streamer/www'

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mjpg_streamer.service
sudo systemctl restart mjpg_streamer.service

sudo journalctl -u mjpg_streamer.service -f
