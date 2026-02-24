@echo off
setlocal
REM Script Batch de teste - Orca
REM Executa e grava data/hora no log

echo Script teste.bat executado em %date% %time%

set LOG_DIR=%~dp0
set LOG_FILE=%LOG_DIR%teste_exec.log
echo Executado em %date% %time% >> "%LOG_FILE%"

exit /b 0
