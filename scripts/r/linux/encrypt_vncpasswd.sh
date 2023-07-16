# In new OpenSSL version, we need to specify -provider legacy for des-cbc encoder
extra_args=''
openssl_version=$(openssl version)
cur_version=$(echo "$openssl_version" | awk '{print $2}')
new_version="3"
if [[ "$(printf '%s\n' "$cur_version" "$new_version" | sort -V | head -n1)" == "$new_version" ]]; then
    extra_args+='-provider legacy'
fi

printf '%-8s' "$1" | tr ' ' '\0' | openssl enc -des-cbc --nopad --nosalt -K e84ad660c4721ae0 -iv 0000000000000000 $extra_args | xxd -p
