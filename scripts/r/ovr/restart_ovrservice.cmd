@echo off

sc config OVRService start= auto

net stop OVRService
taskkill /f /im OVRServer_x64.exe

net start OVRService