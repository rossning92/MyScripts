set -e
mkdir -p "$HOME/.config"
nvim_config=$(realpath "$(dirname "$0")/../../settings/nvim")
ln -f -s "$nvim_config" "$HOME/.config/"
