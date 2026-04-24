# https://github.com/GitHub30/toast-notification-examples

param (
    [string]$bodyText = "Test message",
    [string]$titleText = "myscripts"
)

# ToastText02: A large image, one string of bold text on the first line, one string of regular text on the second line.
$ToastText02 = [Windows.UI.Notifications.ToastTemplateType, Windows.UI.Notifications, ContentType = WindowsRuntime]::ToastText02
$TemplateContent = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]::GetTemplateContent($ToastText02)
$TemplateContent.SelectSingleNode('//text[@id="1"]').InnerText = $titleText
$TemplateContent.SelectSingleNode('//text[@id="2"]').InnerText = $bodyText
$ToastNotification = [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime]::New($TemplateContent)
$ToastNotification.Tag = 'PowerShell'
$AppId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId).Show($ToastNotification)