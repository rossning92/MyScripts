# https://docs.unrealengine.com/5.1/en-US/downloading-unreal-engine-source-code/

set -e

repo="$HOME/Projects/ue5-main"
mkdir -p "$repo"
cd "$repo"

git clone https://github.com/EpicGames/UnrealEngine.git --single-branch -b ue5-main --filter=blob:none .
