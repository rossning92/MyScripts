@echo off
cd /d "{{RENDERDOC_SOURCE}}"
cd "x64\Development"
start qrenderdoc.exe %*
