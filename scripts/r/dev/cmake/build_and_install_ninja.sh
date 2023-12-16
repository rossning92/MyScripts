set -e

GIT_URL=https://github.com/ninja-build/ninja run_script r/git/git_clone.sh

cd ~/Projects/ninja
python3 configure.py --bootstrap
cmake -Bbuild-cmake
cmake --build build-cmake
