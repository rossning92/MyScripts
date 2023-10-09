@ECHO OFF

:: Hide cortana
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v ShowCortanaButton /t REG_DWORD /d 0 /f

:: Never combine taskbar icons
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v TaskbarGlomLevel /t REG_DWORD /d 2 /f

:: Show file extensions
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v HideFileExt /t REG_DWORD /d 0 /f

:: Show hidden files
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v Hidden /t REG_DWORD /d 1 /f

:: Disable explorer search history
reg add HKCU\Software\Policies\Microsoft\Windows\Explorer /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f

:: Hide Task View Icon
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v ShowTaskViewButton /t REG_DWORD /d 0 /f

:: Hide People Icon
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People /v PeopleBand /t REG_DWORD /d 0 /f

:: Set File Explorer to "Open to This PC"
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v LaunchTo /t REG_DWORD /d 1 /f

:: Disable adding frequent folders in Quick access
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer /v ShowFrequent /t REG_DWORD /d 0 /f

:: Remove pinned items from Taskbar
reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband /f
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband\AuxilliaryPins /v MailPin /t REG_DWORD /d 1 /f

:: Disable recent items
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v Start_TrackDocs /t REG_DWORD /d 0 /f
rd /s /q "%APPDATA%\Microsoft\Windows\Recent"

:: Disable Game Bar (Win+G)
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR /v AppCaptureEnabled /t REG_DWORD /d 0 /f
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR /v GameDVR_Enabled /t REG_DWORD /d 0 /f

:: Disable shake to minimize
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v DisallowShaking /t REG_DWORD /d 1 /f

:: Turn off hibernation
powercfg.exe /hibernate off

:: Disable UAC
CALL "%~dp0disable_UAC.cmd"

:: Turn off animation
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_DWORD /d 0 /f
reg add "HKCU\Control Panel\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012078010000000 /f

:: Apply "details" view on all folders
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Streams /v Settings /t REG_BINARY /d 08000000040000000100000000777e137335cf11ae6908002b2e1262040000000200000043000000 /f

:: Customize console window
CALL "%~dp0config_console_window.cmd"

:: Notification duration
reg add "HKCU\Control Panel\Accessibility" /v MessageDuration /t REG_DWORD /d 10 /f

:: Set wallpaper to solid black
reg add "HKCU\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d "" /f
reg add "HKCU\Control Panel\Colors" /v Background /t REG_SZ /d "0 0 0" /f

:: Hide meet now icon
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer /t REG_DWORD /v HideSCAMeetNow /d 1 /f

:: Microsoft Pinyin
reg add HKCU\SOFTWARE\Microsoft\InputMethod\Settings\CHS /t REG_DWORD /v "English Switch Key" /d 4 /f
reg add HKCU\SOFTWARE\Microsoft\InputMethod\Settings\CHS /t REG_DWORD /v EnableChineseEnglishPunctuationSwitch /d 0 /f
reg add HKCU\SOFTWARE\Microsoft\InputMethod\Settings\CHS /t REG_DWORD /v EnableSimplifiedTraditionalOutputSwitch /d 0 /f

taskkill /f /im explorer.exe
start explorer.exe

:: Set default browser manually
@REM "%windir%\system32\control.exe" /name Microsoft.DefaultPrograms /page pageDefaultProgram\pageAdvancedSettings

:: Disable sleep
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0

:: run_script r/win/disable_onedrive.cmd
run_script r/win/disable_auto_updates.cmd
run_script r/win/register_mpv_url_protocal.bat
run_script r/win/disable_windows_animation.ps1
