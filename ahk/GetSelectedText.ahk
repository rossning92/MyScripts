GetSelectedText() {
    clipSaved := ClipboardAll

    Clipboard =
    Send ^c
    ClipWait, 1
    if ErrorLevel {
        Clipboard := clipSaved
        return
    } else {
        text := Clipboard
        Clipboard := clipSaved
        return text
    }
}