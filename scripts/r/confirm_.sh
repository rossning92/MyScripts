read -n1 -p '{{MESSAGE}} (y/n): ' key
echo
[ "$key" = 'y' ] || exit 0
