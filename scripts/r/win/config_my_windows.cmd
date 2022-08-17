@echo off

@REM Hide cortana
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search" /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowCortanaButton /t REG_DWORD /d 0 /f

@REM Never combine taskbar icons
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarGlomLevel /t REG_DWORD /d 2 /f

@REM Show file extensions
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f

@REM Show hidden files
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Hidden /t REG_DWORD /d 1 /f

@REM Disable explorer search history
reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f

@REM Hide Task View Icon
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowTaskViewButton /t REG_DWORD /d 0 /f

@REM Hide Task View Icon
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People" /v PeopleBand /t REG_DWORD /d 0 /f

@REM Set File Explorer to "Open to This PC"
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v LaunchTo /t REG_DWORD /d 1 /f

@REM Remove pinned items from Taskbar
reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband\AuxilliaryPins" /v MailPin /t REG_DWORD /d 1 /f

@REM Disable recent items
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Start_TrackDocs /t REG_DWORD /d 0 /f
rd /s /q "%APPDATA%\Microsoft\Windows\Recent"

@REM Disable Game Bar (Win+G)
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v GameDVR_Enabled /t REG_DWORD /d 0 /f

@REM Disable shake to minimize
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v DisallowShaking /t REG_DWORD /d 1 /f

@REM Turn off hibernation
powercfg.exe /hibernate off

@REM Disable UAC
call %~dp0disable_UAC.cmd

@REM Turn off animation
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_DWORD /d 0 /f
reg add "HKCU\Control Panel\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012078010000000 /f

@REM Apply "details" view on all folders
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Streams /v Settings /t REG_BINARY /d 08000000040000000100000000777e137335cf11ae6908002b2e1262040000000200000043000000 /f

@REM Customize console window
reg add HKCU\Console\%SystemRoot^%_system32_cmd.exe /v CodePage /t REG_DWORD /d 65001 /f

@REM reg add HKCU\Console /v FaceName /t REG_SZ /d Terminal /f
@REM reg add HKCU\Console /v FontFamily /t REG_DWORD /d 0x30 /f
@REM reg add HKCU\Console /v FontSize /t REG_DWORD /d 0xc0008 /f

reg add HKCU\Console /v FaceName /t REG_SZ /d Consolas /f
reg add HKCU\Console /v FontFamily /t REG_DWORD /d 0x36 /f
reg add HKCU\Console /v FontSize /t REG_DWORD /d 0xe0000 /f
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 1 /f

reg add HKCU\Console /v CodePage /t REG_DWORD /d 65001 /f
reg add HKCU\Console /v CtrlKeyShortcutsDisabled /t REG_DWORD /d 1 /f

reg add HKCU\Console /v ColorTable00 /t REG_DWORD /d 0x000c0c0c /f
reg add HKCU\Console /v ColorTable01 /t REG_DWORD /d 0x00da3700 /f
reg add HKCU\Console /v ColorTable02 /t REG_DWORD /d 0x000ea113 /f
reg add HKCU\Console /v ColorTable03 /t REG_DWORD /d 0x00dd963a /f
reg add HKCU\Console /v ColorTable04 /t REG_DWORD /d 0x001f0fc5 /f
reg add HKCU\Console /v ColorTable05 /t REG_DWORD /d 0x00981788 /f
reg add HKCU\Console /v ColorTable06 /t REG_DWORD /d 0x00009cc1 /f
reg add HKCU\Console /v ColorTable07 /t REG_DWORD /d 0x00cccccc /f
reg add HKCU\Console /v ColorTable08 /t REG_DWORD /d 0x00767676 /f
reg add HKCU\Console /v ColorTable09 /t REG_DWORD /d 0x00ff783b /f
reg add HKCU\Console /v ColorTable10 /t REG_DWORD /d 0x000cc616 /f
reg add HKCU\Console /v ColorTable11 /t REG_DWORD /d 0x00d6d661 /f
reg add HKCU\Console /v ColorTable12 /t REG_DWORD /d 0x005648e7 /f
reg add HKCU\Console /v ColorTable13 /t REG_DWORD /d 0x009e00b4 /f
reg add HKCU\Console /v ColorTable14 /t REG_DWORD /d 0x00a5f1f9 /f
reg add HKCU\Console /v ColorTable15 /t REG_DWORD /d 0x00f2f2f2 /f

@REM Notification duration
reg add "HKCU\Control Panel\Accessibility" /v MessageDuration /t REG_DWORD /d 10 /f

@REM Set wallpaper to solid black
reg add "HKCU\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d "" /f
reg add "HKCU\Control Panel\Colors" /v Background /t REG_SZ /d "0 0 0" /f

@REM Hide meet now icon
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /T REG_DWORD /V "HideSCAMeetNow" /D 1 /F

reg add HKCU\Console\%%SystemRoot%%_SYSTEM32_cmd.exe /v CodePage /t REG_DWORD /d 65001 /f

taskkill /f /im explorer.exe
start explorer.exe

@REM Set default browser manually
"%windir%\system32\control.exe" /name Microsoft.DefaultPrograms /page pageDefaultProgram\pageAdvancedSettings

@REM Disable sleep
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0

@REM run_script r/win/disable_onedrive.cmd
run_script r/win/disable_auto_updates.cmd
run_script r/win/register_mpv_url_protocal.bat
run_script r/win/disable_windows_animation.ps1
