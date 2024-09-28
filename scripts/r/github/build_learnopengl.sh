set -e

run_script r/git/git_clone.sh https://github.com/JoeyDeVries/LearnOpenGL
cd ~/Projects/LearnOpenGL

run_script ext/open_code_editor.py .

if [ ! -d "build" ]; then
    mkdir build
    cd build
    cmake -G "Visual Studio 17 2022" ..
else
    cd build
fi

target=$(find . -maxdepth 1 -type f -name "*.vcxproj" -exec basename {} .vcxproj \; | fzf)

while true; do
    if cmake --build . --target "$target"; then
        (
            cd ..
            exe="$(find . -name "$target.exe")"
            cd "$(dirname "$exe")"
            "./$(basename "$exe")" || true
        )
    fi
    read -p "Press Enter key to build and run..."
done
