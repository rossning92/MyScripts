@echo off

taskkill /f /im chrome.exe
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
timeout 5