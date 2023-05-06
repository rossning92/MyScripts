# https://docs.unrealengine.com/5.1/en-US/downloading-unreal-engine-source-code/

set -e

if [[ -n "${UE_SOURCE}" ]]; then
    repo="${UE_SOURCE}"
else
    repo="$HOME/Projects/ue5"
    run_script ext/set_variable.py UE_SOURCE "$repo"
fi

mkdir -p "$repo"
cd "$repo"

git clone https://github.com/EpicGames/UnrealEngine.git --single-branch -b ue5-main --filter=blob:none .
