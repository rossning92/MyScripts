@echo off
set "PATH=C:\tools\socat;%PATH%"
set IPADDR=192.168.0.101

REM netsh wlan connect name=lab-t24103779

taskkill /f /im socat.exe

echo start port forwarding...
start /b socat TCP4-LISTEN:123,fork TCP4:%IPADDR%:22
start /b socat TCP4-LISTEN:5901,fork TCP4:%IPADDR%:5900
