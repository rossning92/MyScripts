#include ../../libs/ahk/ScreenRecord.ahk

g_isRecording := False

F7::
    if not g_isRecording
    {
        SetWindow("A")
        Record()
        g_isRecording := True
    }
    else
    {
        Stop()
        g_isRecording := False
    }
    return