secs=$1
shift
msg=$@
while [ $secs -gt 0 ]; do
    printf "\r\033[KWaiting %.d seconds $msg" $((secs--))
    sleep 1
done
echo
