#!/usr/bin/env bash
set -euo pipefail
PATH=/usr/sbin:/usr/bin:/sbin:/bin

usage="Usage: $(basename "$0") /dev/disk/by-id/DISK_ID [LABEL]"
die() { echo "Error: $*" >&2; exit 1; }

if [[ ${1:-} == -h || ${1:-} == --help ]]; then
    echo "$usage"
    exit
fi
((EUID != 0)) || die "Run as a normal user; sudo is used when needed."
((1 <= $# && $# <= 2)) || die "$usage"

disk_id=$1
label=${2:-backup-1}
[[ $disk_id == /dev/disk/by-id/* ]] || die "Use a stable /dev/disk/by-id path, not /dev/sdX."
[[ -b $disk_id ]] || die "Disk not found: $disk_id"
[[ $label =~ ^[A-Za-z0-9._-]{1,16}$ ]] || die "Label must be 1-16 simple characters."
for cmd in cryptsetup findmnt lsblk mkfs.ext4 parted partprobe udevadm wipefs; do
    command -v "$cmd" >/dev/null || die "Missing command: $cmd"
done

disk=$(readlink -f "$disk_id")
[[ $(lsblk -dnro TYPE "$disk") == disk ]] || die "Target is not a whole disk."
root=$(findmnt -no SOURCE /)
root=$(readlink -f "${root%%[*}")
lsblk -snrpo PATH "$root" | grep -Fxq "$disk" && die "Refusing to erase the system disk."

if lsblk -nrpo MOUNTPOINTS "$disk" | grep -q '[^[:space:]]'; then
    lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS "$disk" >&2
    die "Target contains a mounted filesystem."
fi
while read -r swap; do
    lsblk -snrpo PATH "$swap" | grep -Fxq "$disk" && die "Target contains active swap."
done < <(swapon --noheadings --raw --output NAME 2>/dev/null || true)

serial=$(lsblk -dnro SERIAL "$disk" | tr -d '[:space:]')
[[ -n $serial ]] || die "Disk has no readable serial number."
lsblk -d -o PATH,SIZE,MODEL,SERIAL "$disk"
echo "WARNING: All data on this disk will be permanently erased."
read -r -p "Type serial $serial to continue: " answer
[[ $answer == "$serial" ]] || die "Serial did not match; nothing changed."

mapper="encrypted-$label"
[[ ! -e /dev/mapper/$mapper ]] || die "Mapper already exists: $mapper"
opened=0
trap '((opened)) && sudo cryptsetup close "$mapper" || true' EXIT

sudo -v
sudo wipefs --all "$disk"
sudo parted --script "$disk" mklabel gpt mkpart primary 1MiB 100%
sudo partprobe "$disk"
sudo udevadm settle
partition=$(lsblk -nrpo PATH,TYPE "$disk" | awk '$2 == "part" {print $1; exit}')
[[ -b $partition ]] || die "New partition did not appear."

echo "Enter a new encryption passphrase."
sudo cryptsetup luksFormat --type luks2 --verify-passphrase "$partition"
sudo cryptsetup open "$partition" "$mapper"
opened=1
sudo mkfs.ext4 -L "$label" "/dev/mapper/$mapper"
sudo cryptsetup close "$mapper"
opened=0
trap - EXIT
echo "Ready: LUKS2 $partition, ext4 label $label"
