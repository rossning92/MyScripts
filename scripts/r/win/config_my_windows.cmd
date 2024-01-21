@ECHO OFF

echo Remove the Cortana icon.
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f >NUL
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v ShowCortanaButton /t REG_DWORD /d 0 /f >NUL

echo Never combine taskbar icons.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v TaskbarGlomLevel /t REG_DWORD /d 2 /f >NUL

echo Show file extensions.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v HideFileExt /t REG_DWORD /d 0 /f >NUL

echo Show hidden files.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v Hidden /t REG_DWORD /d 1 /f >NUL

echo Disable explorer search history.
reg add HKCU\Software\Policies\Microsoft\Windows\Explorer /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f >NUL

echo Hide Task View Icon.
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v ShowTaskViewButton /t REG_DWORD /d 0 /f >NUL

echo Hide People Icon.
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People /v PeopleBand /t REG_DWORD /d 0 /f >NUL

echo Set File Explorer to "Open to This PC".
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v LaunchTo /t REG_DWORD /d 1 /f >NUL

echo Disable adding frequent folders in Quick access.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer /v ShowFrequent /t REG_DWORD /d 0 /f >NUL

echo Remove pinned items from Taskbar.
reg delete HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband /f >NUL
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband\AuxilliaryPins /v MailPin /t REG_DWORD /d 1 /f >NUL

echo Disable recent items.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v Start_TrackDocs /t REG_DWORD /d 0 /f >NUL
rd /s /q "%APPDATA%\Microsoft\Windows\Recent"

echo Disable Game Bar (Win+G).
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR /v AppCaptureEnabled /t REG_DWORD /d 0 /f >NUL
reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR /v GameDVR_Enabled /t REG_DWORD /d 0 /f >NUL

echo Disable shake to minimize.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced /v DisallowShaking /t REG_DWORD /d 1 /f >NUL

echo Turn off hibernation.
powercfg.exe /hibernate off

echo Disable UAC.
CALL "%~dp0disable_UAC.cmd"

echo Turn off animation.
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_DWORD /d 0 /f >NUL
reg add "HKCU\Control Panel\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012078010000000 /f >NUL

echo Apply "details" view on all folders.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Streams /v Settings /t REG_BINARY /d 08000000040000000100000000777e137335cf11ae6908002b2e1262040000000200000043000000 /f >NUL

echo Customize console window.
CALL "%~dp0config_console_window.cmd"

echo Notification duration.
reg add "HKCU\Control Panel\Accessibility" /v MessageDuration /t REG_DWORD /d 10 /f >NUL

echo Set wallpaper to solid black.
reg add "HKCU\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d "" /f >NUL
reg add "HKCU\Control Panel\Colors" /v Background /t REG_SZ /d "0 0 0" /f >NUL

echo Remove the Meet Now icon.
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer /t REG_DWORD /v HideSCAMeetNow /d 1 /f >NUL

echo Config Microsoft Pinyin.
reg add HKCU\SOFTWARE\Microsoft\InputMethod\Settings\CHS /t REG_DWORD /v "English Switch Key" /d 4 /f >NUL
reg add HKCU\SOFTWARE\Microsoft\InputMethod\Settings\CHS /t REG_DWORD /v EnableChineseEnglishPunctuationSwitch /d 0 /f >NUL
reg add HKCU\SOFTWARE\Microsoft\InputMethod\Settings\CHS /t REG_DWORD /v EnableSimplifiedTraditionalOutputSwitch /d 0 /f >NUL

echo Disable News and Interests.
reg add HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Feeds /t REG_DWORD /v ShellFeedsTaskbarViewMode /d 2 /f >NUL

TASKKILL /F /IM explorer.exe >NUL
start explorer.exe

@REM echo Set default browser manually.
@REM "%windir%\system32\control.exe" /name Microsoft.DefaultPrograms /page pageDefaultProgram\pageAdvancedSettings

echo Disable the standby timeout.
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0

run_script r/win/disable_auto_updates.cmd
run_script r/win/register_mpv_url_protocal.bat
run_script r/win/disable_windows_animation.ps1
