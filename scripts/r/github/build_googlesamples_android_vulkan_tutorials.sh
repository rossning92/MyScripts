# run_elevated("choco install ninja -y")

BRANCH='' run_script r/git/git_clone.sh https://github.com/googlesamples/android-vulkan-tutorials

cd ~/Projects/android-vulkan-tutorials/tutorial05_triangle

run_script ext/open_code_editor.py .

gradlew installDebug

adb shell am start -n com.google.vulkan.tutorials.five/android.app.NativeActivity
