# Install packages.
required_packages=(g++-multilib ccache)
missing_packages=()
for package in "${required_packages[@]}"; do
    dpkg -s "$package" >/dev/null 2>&1 || missing_packages+=("$package")
done
if [ ${#missing_packages[@]} -ne 0 ]; then
    sudo apt update
    sudo apt-get install -y "${missing_packages[@]}"
fi

# Clone Perfetto repository if it does not exist locally.
mkdir -p ~/Projects
cd ~/Projects
if [[ ! -d perfetto/ ]]; then
    git clone https://android.googlesource.com/platform/external/perfetto/
fi

cd perfetto/
