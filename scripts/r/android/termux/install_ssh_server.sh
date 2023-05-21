pkg install openssh -y
ssh-keygen -A
echo -e "123456\n123456" | passwd
sshd

echo "Please login using: 'ssh $(whoami)@<ip_address> -p 8022' passwd=123456"
