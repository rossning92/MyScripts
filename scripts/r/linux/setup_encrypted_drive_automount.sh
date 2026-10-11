#!/usr/bin/env bash
set -euo pipefail
PATH=/usr/sbin:/usr/bin:/sbin:/bin

# Define shared error and config-file helpers.
usage="Usage: $(basename "$0") DEVICE [NAME]"
die() { echo "Error: $*" >&2; exit 1; }
replace_entry() {
    local file=$1 field=$2 value=$3 line=$4 temp
    temp=$(mktemp)
    sudo awk -v field="$field" -v value="$value" -v line="$line" '
        $1 !~ /^#/ && $field == value {if (!found++) print line; next}
        {print}
        END {if (!found) print line}
    ' "$file" >"$temp"
    sudo install -m 644 "$temp" "$file"
    rm -f "$temp"
}

# Validate arguments and required system tools.
if [[ ${1:-} == -h || ${1:-} == --help ]]; then
    echo "$usage"
    exit
fi
((EUID != 0)) || die "Run as a normal user; sudo is used when needed."
((1 <= $# && $# <= 2)) || die "$usage"

device=$1
name=${2:-encrypted-drive}
[[ -b $device ]] || die "Device not found: $device"
[[ $name =~ ^[A-Za-z0-9._-]+$ ]] || die "Name contains unsupported characters."
for cmd in blkid cryptsetup findmnt lsblk mountpoint systemd-escape; do
    command -v "$cmd" >/dev/null || die "Missing command: $cmd"
done

# Find the LUKS partition and reject a mounted mapping.
partition=$(lsblk -nrpo PATH,FSTYPE "$device" |
    awk '$2 == "crypto_LUKS" {print $1; exit}')
[[ -n $partition ]] || die "No LUKS partition found on $device"
open_mapper=$(lsblk -nrpo PATH,TYPE "$partition" |
    awk '$2 == "crypt" {print $1; exit}')
if [[ -n $open_mapper ]] && findmnt --source "$open_mapper" >/dev/null; then
    die "Unmount the drive before setup."
fi

# Build stable names and confirm permanent system changes.
mapper="auto-$name"
keyfile="/etc/cryptsetup-keys.d/$mapper.key"
mount_dir="/mnt/$name"

echo "Drive: $partition"
echo "Mount: $mount_dir"
echo "Key:   $keyfile"
read -r -p "Type $name to configure automatic unlock: " answer
[[ $answer == "$name" ]] || die "Nothing changed."

# Create a root-only random key and add it to LUKS when needed.
sudo -v
luks_uuid=$(sudo cryptsetup luksUUID "$partition")
crypttab_line="$mapper UUID=$luks_uuid $keyfile luks,nofail"
if [[ -n $open_mapper ]]; then
    sudo cryptsetup close "$(basename "$open_mapper")"
fi
if ! sudo test -f "$keyfile"; then
    sudo install -d -m 700 /etc/cryptsetup-keys.d
    sudo sh -c "umask 077; head -c 64 /dev/urandom > '$keyfile'"
    echo "Enter the current drive passphrase once."
    if ! sudo cryptsetup luksAddKey "$partition" "$keyfile"; then
        sudo rm -f "$keyfile"
        die "Key was not added; key file removed."
    fi
fi

# Unlock temporarily and inspect the inner filesystem.
sudo cryptsetup open --key-file "$keyfile" "$partition" "$mapper"
trap 'sudo cryptsetup close "$mapper" 2>/dev/null || true' EXIT

fs_uuid=$(sudo blkid -s UUID -o value "/dev/mapper/$mapper")
fs_type=$(sudo blkid -s TYPE -o value "/dev/mapper/$mapper")
[[ -n $fs_uuid && -n $fs_type ]] || die "No filesystem found inside LUKS."

# Verify mounting and give the current user ownership.
sudo mkdir -p "$mount_dir"
sudo mount "/dev/mapper/$mapper" "$mount_dir"
sudo chown "$(id -u):$(id -g)" "$mount_dir"
sudo umount "$mount_dir"
sudo cryptsetup close "$mapper"
trap - EXIT

# Register automatic unlock and mounting for future boots.
sudo touch /etc/crypttab
replace_entry /etc/crypttab 1 "$mapper" "$crypttab_line"
fstab_line="UUID=$fs_uuid $mount_dir $fs_type defaults,nofail,x-systemd.device-timeout=10 0 2"
replace_entry /etc/fstab 2 "$mount_dir" "$fstab_line"

# Reload systemd and test the configured unlock and mount units.
sudo systemctl daemon-reload
unit=$(systemd-escape --template=systemd-cryptsetup@.service "$mapper")
mount_unit=$(systemd-escape --path --suffix=mount "$mount_dir")
sudo systemctl restart "$unit"
sudo systemctl start "$mount_unit"
echo "Automatic unlock ready; mounted at $mount_dir"
