@echo off

@REM this does not work and requires a lot of dependencies like android studio
@REM "%UE_SOURCE%\Engine\Extras\Android\SetupAndroid.bat"

@REM https://docs.unrealengine.com/4.27/en-US/SharingAndReleasing/Mobile/Android/Setup/AndroidStudio/
sdkmanager "platform-tools" "platforms;android-28" "build-tools;28.0.3" "cmake;3.10.2.4988404" "ndk;21.1.6352462"

@REM     if os.path.exists(
@REM         r"Engine\Extras\Android\SetupAndroid.bat"
@REM     ):  # NVPACK is deprecated for 5.25+
@REM         call_echo(r"Engine\Extras\Android\SetupAndroid.bat")
@REM     else:
@REM         try:
@REM             setup_nvpack(r"{{NVPACK_ROOT}}")
@REM         except:
@REM             print2("WARNING: NVPACK not found.")
