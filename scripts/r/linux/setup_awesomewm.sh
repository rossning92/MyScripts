set -e

# Install required packages
packages="awesome xbacklight alsa-utils"
for package in $packages; do
    dpkg -s "$package" >/dev/null 2>&1 || {
        sudo apt-get update
        sudo apt-get install -y "$package"
    }
done

# Copy awesome config file
ln -sf "$(dirname "$0")/../../../settings/awesome" $HOME/.config/
