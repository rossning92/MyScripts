set -e
cd ~

# Prerequisite
# sudo apt-get install git fakeroot build-essential ncurses-dev xz-utils libssl-dev bc flex libelf-dev bison -y

# Download Kernel
if [[ ! -f 'linux-5.15.98.tar.xz' ]]; then
    wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.15.98.tar.xz
fi

# Extract the source
tar -xf linux-5.15.98.tar.xz

# Configure the kernel
cd linux-5.15.98/
# make menuconfig

# Copy existing configuration file
cp -v /boot/config-$(uname -r) .config
# make custom changes to the configuration file
# make menuconfig

# Build the Kernel
make
