@echo off

:: Hide cortana
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search" /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowCortanaButton /t REG_DWORD /d 0 /f

:: Never combine taskbar icons
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarGlomLevel /t REG_DWORD /d 2 /f

:: Show file extensions
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f

:: Show hidden files
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Hidden /t REG_DWORD /d 1 /f

:: Disable explorer search history 
reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f

:: Hide Task View Icon
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowTaskViewButton /t REG_DWORD /d 0 /f

:: Hide Task View Icon
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People" /v PeopleBand /t REG_DWORD /d 0 /f

:: Set File Explorer to "Open to This PC"
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v LaunchTo /t REG_DWORD /d 1 /f

:: Remove pinned items from Taskbar
reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband\AuxilliaryPins" /v MailPin /t REG_DWORD /d 0 /f

:: Disable recent items
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Start_TrackDocs /t REG_DWORD /d 0 /f
rd /s /q "%APPDATA%\Microsoft\Windows\Recent"

:: Disable Game Bar (Win+G)
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v GameDVR_Enabled /t REG_DWORD /d 0 /f

:: Disable shake to minimize 
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v DisallowShaking /t REG_DWORD /d 1 /f

:: Turn off hibernation
powercfg.exe /hibernate off

:: Disable UAC
call disable_UAC.cmd

:: Turn off animation
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_DWORD /d 0 /f
reg add "HKCU\Control Panel\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012078010000000 /f

:: Customize console window
reg add HKCU\Console\%SystemRoot^%_system32_cmd.exe /v CodePage /t REG_DWORD /d 65001

reg add HKCU\Console /v CodePage /t REG_DWORD /d 65001 /f
reg add HKCU\Console /v FaceName /t REG_SZ /d Consolas /f
reg add HKCU\Console /v FontSize /t REG_DWORD /d 0x120000 /f
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 1 /f
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

:: Notification duration
reg add "HKCU\Control Panel\Accessibility" /v MessageDuration /t REG_DWORD /d 60 /f

:: Change wallpaper
reg add "HKCU\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d "" /f
reg add "HKCU\Control Panel\Colors" /v Background /t REG_SZ /d "0 0 0" /f

reg add HKCU\Console\%%SystemRoot%%_SYSTEM32_cmd.exe /v CodePage /t REG_DWORD /d 65001 /f

taskkill /f /im explorer.exe
start explorer.exe

:: Set default browser manually
"%windir%\system32\control.exe" /name Microsoft.DefaultPrograms /page pageDefaultProgram\pageAdvancedSettings

:: Disable sleep
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0

run_script /r/win/disable_onedrive.cmd
