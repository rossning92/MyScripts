from _android import run_apk
from _shutil import download

apk = download(
    "https://vulkan.gpuinfo.org/downloads/vulkancapsviewer_4.10_arm.apk",
    save_to_tmp=True,
)
print(apk)
run_apk(apk)
