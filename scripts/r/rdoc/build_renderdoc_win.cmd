@echo off
cd "%USERPROFILE%\Projects\renderdoc"
run_script r/win/msbuild.cmd renderdoc.sln
