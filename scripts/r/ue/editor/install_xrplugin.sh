# https://developers.meta.com/horizon/documentation/unreal/unreal-quick-start-install-metaxr-plugin
cd ~/Downloads
if [[ ! -f UnrealMetaXRPlugin.74.1.zip ]]; then
    curl -L -o UnrealMetaXRPlugin.74.1.zip "https://securecdn-sjc3-1.oculus.com/binaries/download/?id=9602525969785438"
fi
mkdir -p '{{UE_SOURCE}}/Engine/Plugins/Marketplace'
unzip UnrealMetaXRPlugin.74.1.zip -d '{{UE_SOURCE}}/Engine/Plugins/Marketplace'
