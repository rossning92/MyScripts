set -e

# https://github.com/BelfrySCAD/BOSL2/wiki
cd "$HOME/.local/share/OpenSCAD/libraries/"
if [ ! -d "BOSL2" ]; then
    git clone --filter=blob:none --recurse-submodules --single-branch https://github.com/BelfrySCAD/BOSL2
fi

openscad
