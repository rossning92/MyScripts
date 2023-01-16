$ErrorActionPreference = "Stop"

$Config = @"
[wsl2]
networkingMode=bridged
vmSwitch=my-switch
"@

Set-Content "$Env:USERPROFILE\.wslconfig" $Config
wsl --shutdown
