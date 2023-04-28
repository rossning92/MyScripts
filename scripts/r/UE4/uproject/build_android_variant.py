import os

from _android import setup_android_env
from _script import run_script
from UE4.uproject.build_android import build_uproject
from UE4.uproject.config_uproject_for_mobile import config_uproject

if __name__ == "__main__":
    run_script("r/UE4/editor/setup_android.cmd")
    setup_android_env(ndk_version="21.1.6352462")

    project_dir = os.environ["UE_PROJECT_DIR"]

    for multiview in os.environ["_MULTIVIEW_VARIANT"].split():
        for vulkan in os.environ["_VULKAN_VARIANT"].split():
            for msaa in os.environ["_MSAA_VARIANT"].split():
                out_dir = os.path.join(
                    os.environ["UE_BUILD_OUT_DIR"],
                    os.path.basename(project_dir).lower()
                    + ("-vk" if vulkan == "1" else "-gl")
                    + ("-msaa%d" % int(msaa))
                    + ("-multiview" if multiview == "1" else "-doublewide"),
                )

                config_uproject(
                    project_dir,
                    vulkan=vulkan == "1",
                    multiview=multiview == "1",
                    msaa=int(msaa),
                )
                build_uproject(
                    ue_source=r"{{UE_SOURCE}}",
                    project_dir=project_dir,
                    out_dir=out_dir,
                    compile_cpp=True,
                )
