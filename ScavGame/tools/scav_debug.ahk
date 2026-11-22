#Requires AutoHotkey v2.0
log := A_ScriptDir "\ahk.log"
try FileDelete(log)
try {
    id := WinExist("ahk_exe Probably Stolen.exe")
    FileAppend("id=" id " title=[" WinGetTitle("ahk_id " id) "]`n", log)
    WinActivate("ahk_id " id)
    Sleep 1200
    FileAppend("active=" WinActive("ahk_id " id) "`n", log)
    FileAppend("fgtitle=[" WinGetTitle("A") "]`n", log)
} catch as e {
    FileAppend("err=" e.Message "`n", log)
}
