# Script PowerShell de teste - Orca
# Executa e grava data/hora no log

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "Script teste.ps1 executado em $timestamp"

$logDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = Join-Path $logDir "teste_exec.log"
"Executado em $timestamp" | Out-File -FilePath $logFile -Append -Encoding utf8

exit 0
