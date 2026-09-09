' PrincePDF Silent Windows Launcher
' Launches PrincePDF using pythonw.exe without displaying any console window.
Dim objShell, strArgs, i, cmd, fso, currentDir, pythonwPath

Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonwPath = "pythonw.exe"

strArgs = ""
For i = 0 To WScript.Arguments.Count - 1
    strArgs = strArgs & " """ & WScript.Arguments(i) & """"
Next

cmd = """" & currentDir & "\main.py""" & strArgs
objShell.Run pythonwPath & " " & cmd, 0, False
