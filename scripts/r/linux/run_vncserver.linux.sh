if ! [ -x "$(command -v x0vncserver)" ]; then
    sudo apt update
    sudo apt-get install tigervnc-scraping-server -y
fi

killall x0vncserver || true
x0vncserver -localhost no -passwordfile ~/.vnc/passwd -display :0
