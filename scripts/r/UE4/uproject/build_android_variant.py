import os

from _android import setup_android_env
from _script import run_script
from UE4.uproject.build_android import build_uproject
from UE4.uproject.config_uproject_for_mobile import config_uproject
from _unrealcommon import get_unreal_source_version


if __name__ == "__main__":
    run_script("r/UE4/editor/setup_android.cmd")
    setup_android_env(ndk_version="21.1.6352462")
    ue_version = get_unreal_source_version()

    project_dir = os.environ["UE_PROJECT_DIR"]
    for vulkan in os.environ["_VULKAN_VARIANT"].split():
        name = (
            f"{os.path.basename(project_dir).lower()}-{ue_version}"
            f"{'-vk' if vulkan == '1' else '-gl'}"
        )
        out_dir = os.path.join(
            os.environ["UE_ANDROID_OUT_DIR"],
            name,
        )

        config_uproject(
            project_dir,
            vulkan=vulkan == "1",
            update_package_name=True,
        )
        build_uproject(
            ue_source=r"{{UE_SOURCE}}",
            project_dir=project_dir,
            out_dir=out_dir,
            compile_cpp=True,
        )
