#NoTrayIcon
#SingleInstance Force

$>!h::SendEmoji("😃")
$>!s::SendEmoji("😞")
$>!w::SendEmoji("😉")
$>!k::SendEmoji("😏")
$>!y::SendEmoji("👍")
$>!t::SendEmoji("😛")
$>!m::SendEmoji("🙂")
$>!u::SendEmoji("☂️")

SendEmoji(s)
{
    Send %s%
    ; clipSave := ClipboardAll
    ; Clipboard := s
    ; Send, ^v
    ; Clipboard := clipSave
}
