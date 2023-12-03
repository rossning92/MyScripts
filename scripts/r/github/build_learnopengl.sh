set -e

run_script r/git/git_clone.sh https://github.com/JoeyDeVries/LearnOpenGL
cd ~/Projects/LearnOpenGL

mkdir -p build
(
    cd build
    cmake -G "Visual Studio 16 2019" ..

    target=$(find . -maxdepth 1 -type f -name "*.vcxproj" -exec basename {} .vcxproj \; | fzf)
    cmake --build . --target "$target"
)

run_script ext/open_code_editor.py .
# run_script ext/open.py LearnOpenGL.sln
