run_script r/git/git_clone.py https://github.com/JoeyDeVries/LearnOpenGL
cd ~/Projects/LearnOpenGL

cmd.exe
(
    mkdir -p build
    cd build
    cmake -G "Visual Studio 16 2019" ..
    cmd.exe /c "LearnOpenGL.sln"
)
