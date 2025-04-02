set -e

repo="${UE_SOURCE}"
branch="${UE_BRANCH:-oculus-5.5}"

echo "Cloning to ${repo}"
mkdir -p "$repo"
cd "$repo"

# https://developers.meta.com/horizon/documentation/unreal/unreal-quick-start-install-unreal-engine#meta-fork
git clone https://github.com/Oculus-VR/UnrealEngine --single-branch -b $branch --filter=blob:none .

run_script r/ue/editor/install_xrplugin.sh
