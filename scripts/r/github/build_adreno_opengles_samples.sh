set -e
run_script r/git/git_clone.sh https://github.com/quic/adreno-gpu-opengl-es-code-sample-framework

cd ~/Projects/adreno-gpu-opengl-es-code-sample-framework/samples/shading_rate/build/android
gradle wrapper --gradle-version 6.1.1
./gradlew.bat assembleDebug
