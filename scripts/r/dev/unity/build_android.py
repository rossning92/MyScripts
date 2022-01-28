from _shutil import call_echo, find_newest_file

if __name__ == "__main__":
    unity = find_newest_file(r"C:\Program Files\Unity\Hub\Editor\**\Editor\Unity.exe")

    # set UNITY_PROJECT_PATH="{{UNITY_PROJECT_PATH}}"
    # set UNITY_OUTPUT_EXE="{{UNITY_PROJECT_PATH}}\Build\Build.exe"
    # set UNITY_LOG="%LOCALAPPDATA%\Unity\Editor\Editor.log"

    # -buildWindows64Player %UNITY_OUTPUT_EXE% -quit

    call_echo(
        [
            unity,
            # "-batchmode",
            "-projectPath",
            r"{{UNITY_PROJECT_PATH}}",
            "-buildTarget",
            "Android",
        ]
    )
