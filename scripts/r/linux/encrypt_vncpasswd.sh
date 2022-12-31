printf '%-8s' "$1" | tr ' ' '\0' | openssl enc -des-cbc --nopad --nosalt -K e84ad660c4721ae0 -iv 0000000000000000 | xxd -p
