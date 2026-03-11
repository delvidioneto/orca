@echo off
REM Remove o Orca do Iniciar do Windows (o Django nao subira mais automaticamente ao ligar o PC).

reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Orca /f 2>nul
if errorlevel 1 (
    echo Orca nao estava no Iniciar do Windows.
) else (
    echo Orca removido do Iniciar do Windows.
)
echo.
pause
