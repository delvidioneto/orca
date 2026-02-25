' Inicia o Orca em segundo plano (sem janela CMD visível).
' Coloque junto de IniciarOrca.bat na raiz do projeto.
' Para parar: use PararOrca.bat ou encerre python.exe no Gerenciador de Tarefas.

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dirBat = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = fso.BuildPath(dirBat, "IniciarOrca.bat")

' Executa o .bat com janela oculta (0 = hidden)
sh.Run "cmd /c """ & batPath & """", 0, False
