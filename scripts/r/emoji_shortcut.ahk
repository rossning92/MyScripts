#SingleInstance Force

$>!h::SendEmoji("😃")
$>!s::SendEmoji("😢")
$>!w::SendEmoji("😉")
$>!k::SendEmoji("😏")
$>!y::SendEmoji("👍")

SendEmoji(s)
{
    clipSave := ClipboardAll
    Clipboard := s
    Send, ^v
    Clipboard := clipSave
}
