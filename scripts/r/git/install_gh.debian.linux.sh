if [ ! -f /etc/apt/sources.list.d/github-cli.list ]; then
    type -p wget >/dev/null || (sudo apt update && sudo apt install -y wget)
    sudo mkdir -p -m 755 /etc/apt/keyrings

    github_cli_keyring=$(mktemp)
    wget -nv -O "$github_cli_keyring" https://cli.github.com/packages/githubcli-archive-keyring.gpg
    sudo install -m 644 "$github_cli_keyring" /etc/apt/keyrings/githubcli-archive-keyring.gpg
    rm "$github_cli_keyring"

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" |
        sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
    sudo apt update
fi

sudo apt install -y gh
