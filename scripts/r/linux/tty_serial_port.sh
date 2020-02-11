if ! [ -x "$(command -v minicom)" ]; then
  sudo apt-get install minicom -y
fi

minicom -b 115200 -8 -D /dev/{{_DEV}}
