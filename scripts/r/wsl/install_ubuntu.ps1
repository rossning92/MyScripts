cd "$env:USERPROFILE\Downloads"

if(!(Test-Path Ubuntu.appx))
{
    Invoke-WebRequest -Uri https://aka.ms/wslubuntu2004 -OutFile Ubuntu.appx -UseBasicParsing
}

.\Ubuntu.appx