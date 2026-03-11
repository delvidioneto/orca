@echo off
setlocal
REM Script Batch de teste - Orca (install/windows)
REM Executa e grava data/hora no log. ROOT = raiz do projeto.

cd /d "%~dp0..\.."
set "ROOT=%CD%"

echo Script teste.bat executado em %date% %time%

set "LOG_FILE=%ROOT%\scripts\teste_exec.log"
echo Executado em %date% %time% >> "%LOG_FILE%"

exit /b 0
