@echo off
REM Encerra o servidor Orca (manage.py runserver) iniciado em segundo plano.

echo Parando Orca...
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%runserver%%'" get processid 2^>nul ^| findstr [0-9]') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo Pronto.
timeout /t 2 >nul
