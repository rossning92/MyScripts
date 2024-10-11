set -e
cd "$(dirname "$0")"
for dir in */; do
    echo "Installing extension: ${dir%/}"
    run_script r/dev/vscode/install_vscode_extension.py "${dir%/}"
done