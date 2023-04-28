import os
import shutil
import subprocess
import sys

from _shutil import call_echo, find_newest_file

if __name__ == "__main__":
    unity = find_newest_file(r"C:\Program Files\Unity\Hub\Editor\**\Editor\Unity.exe")
    if unity is None:
        unity = find_newest_file(r"C:\Program Files\Unity*\Editor\Unity.exe")

    # if sys.platform == "win32":
    #     subprocess.call(["taskkill", "/f", "/im", "Unity.exe"])

    project_dir = os.environ["UNITY_PROJECT_PATH"]

    # Copy build script
    target_build_script = os.path.join(
        project_dir, "Assets", "Editor", "AndroidBuildScript.cs"
    )
    os.makedirs(os.path.dirname(target_build_script), exist_ok=True)
    shutil.copy("AndroidBuildScript.cs", target_build_script)

    # Output apk
    project_name = os.path.basename(project_dir)
    os.makedirs(f"/tmp/{project_name}", exist_ok=True)
    os.environ["UNITY_OUTPUT_APK"] = f"/tmp/{project_name}/{project_name}.apk"

    call_echo(
        [
            unity,
            # "-batchmode",
            "-projectPath",
            project_dir,
            "-buildTarget",
            "Android",
            "-executeMethod",
            "AndroidBuildScript.BuildAndroid",
            # "-quit",
        ]
    )
