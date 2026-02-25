@echo off
REM Iniciador completo do Orca para Windows - .venv, pip, migrate, runserver
REM Para rodar em segundo plano (sem janela): use IniciarOrca.vbs
REM Requisito: Python instalado no PATH (python ou py).

cd /d "%~dp0"
set ROOT=%~dp0
if "%ROOT:~-1%"=="\" set ROOT=%ROOT:~0,-1%

REM Remove arquivo de erro de execução anterior
if exist "%ROOT%orca_err.txt" del "%ROOT%orca_err.txt"

echo.
echo === Orca - Iniciador ===
echo.

REM 1) Python do sistema (para criar .venv se precisar)
set SYS_PY=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set SYS_PY=python
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set SYS_PY=py -3
    )
)
if "%SYS_PY%"=="" (
    echo Python nao encontrado. Instale Python e adicione ao PATH. > "%ROOT%orca_err.txt"
    echo https://www.python.org/downloads/ >> "%ROOT%orca_err.txt"
    pause
    exit /b 1
)

REM 2) Criar .venv se nao existir
if not exist "%ROOT%\.venv\Scripts\python.exe" (
    echo [1/4] Criando .venv...
    "%SYS_PY%" -m venv "%ROOT%\.venv"
    if errorlevel 1 (
        echo Erro ao criar .venv. >> "%ROOT%orca_err.txt"
        pause
        exit /b 1
    )
    echo .venv criado.
) else (
    echo [1/4] .venv ja existe.
)
set "PY=%ROOT%\.venv\Scripts\python.exe"

REM 3) Instalar dependencias (requirements.txt)
echo.
echo [2/4] Verificando dependencias (pip install)...
"%PY%" -m pip install -r "%ROOT%\requirements.txt" -q 2>nul
if errorlevel 1 (
    "%PY%" -m pip install -r "%ROOT%\requirements.txt"
    if errorlevel 1 (
        echo Erro ao instalar dependencias. >> "%ROOT%orca_err.txt"
        pause
        exit /b 1
    )
)
echo Dependencias OK.

REM 4) Migrações
echo.
echo [3/4] Executando migracoes (manage.py migrate)...
set DATABASE=sqlite
"%PY%" "%ROOT%\manage.py" migrate --noinput
if errorlevel 1 (
    echo Erro ao rodar migrate. >> "%ROOT%orca_err.txt"
    pause
    exit /b 1
)
echo Migracoes OK.

REM 5) Servidor
echo.
echo [4/4] Iniciando servidor...
echo.
echo Acesse: http://127.0.0.1:8000
echo Para parar: feche esta janela ou use PararOrca.bat
echo.
"%PY%" "%ROOT%\manage.py" runserver 0.0.0.0:8000
pause
