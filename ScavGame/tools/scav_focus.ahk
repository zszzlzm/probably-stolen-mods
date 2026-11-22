#Requires AutoHotkey v2.0
WinActivate("Probably Stolen")
if !WinWaitActive("Probably Stolen", , 5)
    ExitApp 2
Sleep 500
Send("{Esc}")
Sleep 700
Send("{Esc}")
Sleep 700
