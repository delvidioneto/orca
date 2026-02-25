@echo off
REM Adiciona o Orca ao Iniciar do Windows. Ao ligar o PC e fazer login, o Django sobe automaticamente em segundo plano.
REM Execute uma vez. Para remover: use RemoverInicioWindows.bat

set "VBS=%~dp0IniciarOrca.vbs"
if not exist "%VBS%" (
    echo Arquivo nao encontrado: IniciarOrca.vbs
    echo Coloque este .bat na mesma pasta do IniciarOrca.vbs.
    pause
    exit /b 1
)

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Orca /t REG_SZ /d "wscript.exe \"%VBS%\"" /f
if errorlevel 1 (
    echo Erro ao adicionar ao Registro.
    pause
    exit /b 1
)

echo.
echo Orca foi adicionado ao Iniciar do Windows.
echo Ao fazer login, o servidor subira automaticamente em segundo plano.
echo Para remover: execute RemoverInicioWindows.bat
echo.
pause
