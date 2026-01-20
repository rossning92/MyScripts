from _shutil import download
from utils.android import run_apk

apk = download(
    "https://vulkan.gpuinfo.org/downloads/vulkancapsviewer_4.10_arm.apk",
    save_to_tmp=True,
)
print(apk)
run_apk(apk)
