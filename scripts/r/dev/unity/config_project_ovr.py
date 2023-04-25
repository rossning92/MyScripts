import os

from unityparser import UnityDocument

d = r"C:\Users\rossning92\HelloUnity"

p = os.path.join(d, "ProjectSettings", "ProjectSettings.asset")
doc = UnityDocument.load_yaml(p)

doc.entry.defaultScreenOrientation = 3
doc.entry.m_StereoRenderingPath = 2
doc.entry.m_ActiveColorSpace = 1  # linear
doc.entry.AndroidMinSdkVersion = 29  # Android 10
doc.entry.AndroidPreferredInstallLocation = 0  # auto
doc.entry.AndroidTargetArchitectures = 2  # arm64

# vulkan
for item in doc.entry.m_BuildTargetGraphicsAPIs:
    if item["m_BuildTarget"] == "AndroidPlayer":
        item["m_APIs"] = 15000000
        item["m_Automatic"] = 0
        break

doc.entry.scriptingBackend["Android"] = 1  # IL2CPP scripting backend

doc.dump_yaml(p)
