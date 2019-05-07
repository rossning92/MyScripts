#SingleInstance Force

$!h::SendEmoji("😃")
$!s::SendEmoji("😢")

SendEmoji(s)
{
    clipSave := ClipboardAll
    Clipboard := s
    Send, ^v
    Clipboard := clipSave
}