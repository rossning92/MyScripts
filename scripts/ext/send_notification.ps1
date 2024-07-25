param (
    [string]$Message = "Test message"
)

[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipText = $Message
$notify.Visible = $True
$notify.ShowBalloonTip(3000)