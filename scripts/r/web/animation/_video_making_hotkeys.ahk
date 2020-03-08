#SingleInstance, Force

PROJ_DIR = C:\Data\how_to_make_video

if not WinExist("r/audio/recorder")
{
    EnvSet, RECORD_OUT_DIR, %PROJ_DIR%\record
    Run ..\..\..\..\bin\run_script /r/audio/recorder
}
