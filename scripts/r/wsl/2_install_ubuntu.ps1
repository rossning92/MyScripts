cd "$env:USERPROFILE\Downloads"

if(!(Test-Path Ubuntu.appx))
{
    Invoke-WebRequest -Uri https://aka.ms/wsl-ubuntu-1604 -OutFile Ubuntu.appx -UseBasicParsing
}

.\Ubuntu.appx