@echo off
set VENV_DIR=.venv
set TEST_SCRIPT=python/test_conexao.py
set CLIENT_SCRIPT=python/client_gui.py

echo.
echo =======================================================
echo     INICIANDO SISTEMA ACADEMICO (MAQUINA 2)
echo =======================================================
echo.

cd /d %~dp0

if not exist %VENV_DIR%\Scripts\activate (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Execute install_dependencias.bat primeiro.
    pause
    exit /b 1
)

call %VENV_DIR%\Scripts\activate
echo Ativado ambiente virtual: %VENV_DIR%
echo.

echo =======================================================
echo     TESTANDO CONEXAO COM O SERVIDOR (MAQUINA 1)
echo =======================================================
echo.

python %TEST_SCRIPT%
if errorlevel 1 (
    echo.
    echo FALHA NA CONEXAO. Sistema nao sera iniciado.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo     CONEXAO OK. INICIANDO APLICATIVO...
echo =======================================================
echo.

start python %CLIENT_SCRIPT%

timeout /t 2 /nobreak >nul

echo.
echo Sistema iniciado com sucesso!
echo A janela do aplicativo deve estar aberta.
echo.

exit /b 0
