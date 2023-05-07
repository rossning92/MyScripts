# https://docs.unrealengine.com/5.1/en-US/downloading-unreal-engine-source-code/

set -e

version=5.1

if [[ -n "${UE_SOURCE}" ]]; then
    repo="${UE_SOURCE}"
else
    repo="C:\Projects\ue${version}"
    if [[ -n "${_CLONE_OVR_FORK}" ]]; then
        repo+='-ovr'
    fi
    run_script ext/set_variable.py UE_SOURCE "$repo"
fi

echo "Cloning to ${repo}"
mkdir -p "$repo"
cd "$repo"
if [[ -n "${_CLONE_OVR_FORK}" ]]; then
    git clone https://github.com/Oculus-VR/UnrealEngine --single-branch -b oculus-$version --filter=blob:none .
else
    git clone https://github.com/EpicGames/UnrealEngine.git --single-branch -b $version --filter=blob:none .
fi
