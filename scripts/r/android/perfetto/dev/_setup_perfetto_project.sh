# Install all required packages
required_packages=(g++-multilib ccache)
for package in "${required_packages[@]}"; do
    if ! dpkg -s "$package" >/dev/null 2>&1; then
        echo "$package"
        sudo apt-get install -y "$package"
    fi
done

# Clone repo
mkdir -p ~/Projects
cd ~/Projects
if [[ ! -d perfetto/ ]]; then
    git clone https://android.googlesource.com/platform/external/perfetto/
fi

cd perfetto/
