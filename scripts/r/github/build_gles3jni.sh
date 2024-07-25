set -e
run_script r/git/git_clone.sh https://github.com/googlesamples/android-ndk
cd ~/Projects/android-ndk

./gradlew :gles3jni:app:installDebug
adb shell am start -n com.android.gles3jni/.GLES3JNIActivity
