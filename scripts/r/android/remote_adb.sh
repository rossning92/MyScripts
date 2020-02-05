echo 'Connect to remote adb... (Ctrl-C to close)'
ssh -N -L 5037:127.0.0.1:5037 {{_HOST_IP}}