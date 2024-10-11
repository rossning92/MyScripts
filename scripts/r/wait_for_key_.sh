read -n1 -p '{{MESSAGE}} (y/n): ' key
echo
if [[ "$key" != 'y' ]]; then
    exit 1
fi
