# https://docs.unrealengine.com/5.1/en-US/downloading-unreal-engine-source-code/
# https://developer.oculus.com/documentation/unreal/unreal-quick-start-guide-quest/

set -e

repo="${UE_SOURCE}"
branch="$UE_BRANCH"

echo "Cloning to ${repo}"
mkdir -p "$repo"
cd "$repo"

git clone https://github.com/Oculus-VR/UnrealEngine --single-branch -b $branch --filter=blob:none .
