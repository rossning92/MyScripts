@echo off
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d 127.0.0.1:1234 /f
reg add "HKCU\Software\Policies\Microsoft\Internet Explorer\Control Panel" /v Proxy /t REG_DWORD /d 1 /f