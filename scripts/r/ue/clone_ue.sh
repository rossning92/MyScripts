# https://docs.unrealengine.com/5.1/en-US/downloading-unreal-engine-source-code/
# https://github.com/Oculus-VR/UnrealEngine

set -e

if [[ -z "${UE_VERSION}" ]]; then
    UE_VERSION=5.4
fi

if [[ -n "${UE_SOURCE}" ]]; then
    repo="${UE_SOURCE}"
else
    repo="C:\Projects\ue${UE_VERSION}"
    if [[ -n "${UE_CLONE_OVR_FORK}" ]]; then
        repo+='-ovr'
    fi
    run_script ext/set_variable.py UE_SOURCE "$repo"
fi

echo "Cloning to ${repo}"
mkdir -p "$repo"
cd "$repo"
if [[ -n "${UE_CLONE_OVR_FORK}" ]]; then
    if [[ "$UE_VERSION" = "5*" ]]; then
        branch=oculus-$UE_VERSION
    else
        branch=$UE_VERSION
    fi
    git clone https://github.com/Oculus-VR/UnrealEngine --single-branch -b $branch --filter=blob:none .
else
    git clone https://github.com/EpicGames/UnrealEngine.git --single-branch -b $UE_VERSION --filter=blob:none .
fi
