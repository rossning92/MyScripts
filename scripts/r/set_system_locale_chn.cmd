@echo off

reg add "HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage" /v OEMCP /t REG_SZ /d 936 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Nls\Language" /ve /t REG_SZ /d 0804 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Nls\Locale" /ve /t REG_SZ /d 00000804 /f
