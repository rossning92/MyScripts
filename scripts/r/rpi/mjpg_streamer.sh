set -e

if [ ! -d "mjpg-streamer-master" ]; then
    wget https://github.com/jacksonliam/mjpg-streamer/archive/master.zip
    unzip master.zip
    rm master.zip
fi

cd mjpg-streamer-master/mjpg-streamer-experimental

if [ ! -f "input_uvc.so" ]; then
    sudo apt-get install cmake libjpeg8-dev -y
    sudo apt-get install gcc g++ -y
    make
    sudo make install
fi

mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x480" -o "output_http.so -w ./www"
