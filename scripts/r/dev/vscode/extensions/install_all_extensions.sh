set -e
cd "$(dirname "$0")"
for dir in */; do
    if [ -f "${dir}package.json" ]; then
        echo "Installing local extension: ${dir%/}"
        run_script r/dev/vscode/install_vscode_extension.py "${dir%/}"
    fi
done
