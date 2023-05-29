set -e
pkg install squid -y

echo 'Write /usr/etc/squid/squid.conf'
cat >/data/data/com.termux/files/usr/etc/squid/squid.conf <<EOF
http_port 3128
http_access allow all
EOF

if ! grep -qF -- "squid" ~/.bashrc; then
    echo "Add squid to bashrc"
    echo "squid" >>~/.bashrc
fi

killall -9 squid
squid
