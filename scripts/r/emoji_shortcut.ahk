#SingleInstance Force

$!h::SendEmoji("😃")
$!s::SendEmoji("😢")
$!t::SendEmoji("😉")

SendEmoji(s)
{
    clipSave := ClipboardAll
    Clipboard := s
    Send, ^v
    Clipboard := clipSave
}
