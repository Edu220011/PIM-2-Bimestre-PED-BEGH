@echo off
set "VENV_DIR=conexao\.venv"  :: Sobe DOIS níveis para a RAIZ
set "SERVER_SCRIPT=conexao\maq1\server.py" :: Corrigido: Está na mesma pasta

echo.
echo =======================================================
echo     🌐 INICIANDO SERVIDOR PROXY (MAQUINA 1)
echo =======================================================
echo.

pushd "%~dp0"

echo ** VERIFICANDO CAMINHOS... **
echo Caminho do .bat: %CD%
echo.

:: Ativa o ambiente virtual (Caminho permanece ..\..\.venv)
if not exist "%VENV_DIR%\Scripts\activate" (
    echo.
    echo ❌ ERRO FATAL: Ambiente virtual nao encontrado.
    echo.
    echo -> CAMINHO PROCURADO RELATIVAMENTE: "%VENV_DIR%\Scripts\activate"
    pause
    popd
    exit /b 1
)

echo Ativando ambiente virtual...
call "%VENV_DIR%\Scripts\activate"

echo Ativado ambiente virtual: %VENV_DIR%
echo Rodando servidor: %SERVER_SCRIPT%
echo.

:: Executa o script do servidor
python "%SERVER_SCRIPT%"

popd
pause