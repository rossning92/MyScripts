@ECHO OFF

@REM Customize console window
reg add HKCU\Console /v CodePage /t REG_DWORD /d 65001 /f
reg add HKCU\Console\%SystemRoot^%_SYSTEM32_cmd.exe /v CodePage /t REG_DWORD /d 65001 /f
reg add HKCU\Console /v CtrlKeyShortcutsDisabled /t REG_DWORD /d 1 /f
reg add HKCU\Console /v FaceName /t REG_SZ /d Consolas /f
reg add HKCU\Console /v FontFamily /t REG_DWORD /d 0x36 /f
reg add HKCU\Console /v FontSize /t REG_DWORD /d 0xe0000 /f
reg add HKCU\Console /v InsertMode /t REG_DWORD /d 1 /f
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 1 /f
@REM use ctrl+shift+c/v to copy and paste
reg add HKCU\Console /v InterceptCopyPaste /t REG_DWORD /d 1 /f

@REM Terminal colors
reg add HKCU\Console /v ColorTable00 /t REG_DWORD /d 0x00362a28 /f
reg add HKCU\Console /v ColorTable01 /t REG_DWORD /d 0x00bc4354 /f
reg add HKCU\Console /v ColorTable02 /t REG_DWORD /d 0x003dde66 /f
reg add HKCU\Console /v ColorTable03 /t REG_DWORD /d 0x00fbd677 /f
reg add HKCU\Console /v ColorTable04 /t REG_DWORD /d 0x003c3cee /f
reg add HKCU\Console /v ColorTable05 /t REG_DWORD /d 0x00f993bd /f
reg add HKCU\Console /v ColorTable06 /t REG_DWORD /d 0x006cb8ff /f
reg add HKCU\Console /v ColorTable07 /t REG_DWORD /d 0x00f2f8f8 /f
reg add HKCU\Console /v ColorTable08 /t REG_DWORD /d 0x005a4744 /f
reg add HKCU\Console /v ColorTable09 /t REG_DWORD /d 0x00a47262 /f
reg add HKCU\Console /v ColorTable10 /t REG_DWORD /d 0x007bfa50 /f
reg add HKCU\Console /v ColorTable11 /t REG_DWORD /d 0x00fde98b /f
reg add HKCU\Console /v ColorTable12 /t REG_DWORD /d 0x005555ff /f
reg add HKCU\Console /v ColorTable13 /t REG_DWORD /d 0x00c679ff /f
reg add HKCU\Console /v ColorTable14 /t REG_DWORD /d 0x008cfaf1 /f
reg add HKCU\Console /v ColorTable15 /t REG_DWORD /d 0x00f2f8f8 /f

@REM Window size
reg add HKCU\Console /v WindowSize /t REG_DWORD /d 0x190050 /f