# https://developers.meta.com/horizon/documentation/unreal/unreal-quick-start-install-metaxr-plugin
cd ~/Downloads
zipfile=UnrealMetaXRPlugin.72.0.zip
if [[ ! -f "$zipfile" ]]; then
    # https://developers.meta.com/horizon/downloads/package/unreal-engine-5-integration
    curl -L -o "$zipfile" "https://securecdn-sjc3-1.oculus.com/binaries/download/?id=9233924603312245" #72
fi
rm -rf '{{UE_SOURCE}}/Engine/Plugins/Marketplace' || true
mkdir -p '{{UE_SOURCE}}/Engine/Plugins/Marketplace'
unzip "$zipfile" -d '{{UE_SOURCE}}/Engine/Plugins/Marketplace'
