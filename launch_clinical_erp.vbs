Dim WshShell, FSO, ScriptDir
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Dynamically discover the folder where this VBScript is located
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' Set the working environment path to this folder natively within the script host
WshShell.CurrentDirectory = ScriptDir

' Launch Streamlit invisibly using python -m execution
WshShell.Run "cmd.exe /c python -m streamlit run clinic_erp.py --server.port 8510", 0, False

Set WshShell = Nothing
Set FSO = Nothing