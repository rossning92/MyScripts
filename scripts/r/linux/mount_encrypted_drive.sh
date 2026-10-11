#!/usr/bin/env bash
set -euo pipefail
PATH=/usr/sbin:/usr/bin:/sbin:/bin

usage="Usage: $(basename "$0") DEVICE"
die() { echo "Error: $*" >&2; exit 1; }

if [[ ${1:-} == -h || ${1:-} == --help ]]; then
    echo "$usage"
    exit
fi
[[ $# == 1 ]] || die "$usage"
[[ -b $1 ]] || die "Device not found: $1"
command -v udisksctl >/dev/null || die "Missing command: udisksctl"

partition=$(lsblk -nrpo PATH,FSTYPE "$1" |
    awk '$2 == "crypto_LUKS" {print $1; exit}')
[[ -n $partition ]] || die "No LUKS partition found on $1"

mapper=$(lsblk -nrpo PATH,TYPE "$partition" |
    awk '$2 == "crypt" {print $1; exit}')
if [[ -z $mapper ]]; then
    udisksctl unlock --block-device "$partition"
    udevadm settle
    mapper=$(lsblk -nrpo PATH,TYPE "$partition" |
        awk '$2 == "crypt" {print $1; exit}')
fi
[[ -n $mapper ]] || die "Drive unlocked, but mapped filesystem was not found."

mountpoint=$(findmnt -nr -o TARGET --source "$mapper" || true)
if [[ -z $mountpoint ]]; then
    udisksctl mount --block-device "$mapper"
    mountpoint=$(findmnt -nr -o TARGET --source "$mapper")
fi
echo "Mounted at $mountpoint"
