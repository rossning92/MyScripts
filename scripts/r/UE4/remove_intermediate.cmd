@echo off
cd /d "{{UE_SOURCE}}"

choice /c YN
if %errorlevel%==1 goto (
	rd Engine\Intermediate /s /q
)
