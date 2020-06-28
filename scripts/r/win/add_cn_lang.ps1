$langList = Get-WinUserLanguageList
$langList.Add("zh-CN")
Set-WinUserLanguageList $langList -Force
