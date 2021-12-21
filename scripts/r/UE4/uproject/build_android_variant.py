import os

from UE4.config_for_mobile import config_uproject
from UE4.uproject.build_android import build_uproject

project_dir = r"{{UE4_PROJECT_DIR}}"
msaa_variant = [4]
multiview_variant = [True]
vulkan_variant = [False, True]


if __name__ == "__main__":
    for multiview in multiview_variant:
        for vulkan in vulkan_variant:
            for msaa in msaa_variant:
                out_dir = (
                    "/tmp/"
                    + os.path.basename(project_dir).lower()
                    + ("-vk" if vulkan else "-gl")
                    + ("-msaa%d" % msaa)
                    + ("-multiview" if multiview else "-doublewide")
                )

                config_uproject(
                    project_dir, vulkan=vulkan, multiview=multiview, msaa=msaa
                )
                build_uproject(
                    ue_source=r"{{UE_SOURCE}}",
                    project_dir=project_dir,
                    out_dir=out_dir,
                )
