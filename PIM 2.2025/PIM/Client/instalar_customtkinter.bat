@echo off
REM ========================================
REM  INSTALAR CUSTOMTKINTER - CLIENTE
REM ========================================

echo.
echo ====================================================
echo  INSTALADOR CUSTOMTKINTER - PED-BEGH
echo ====================================================
echo.

REM Verificar se estamos no diretório correto
if not exist "python" (
    echo [ERRO] Pasta python não encontrada!
    echo.
    echo Execute este arquivo dentro de: Client\
    echo.
    pause
    exit /b 1
)

REM Mudar para o diretório correto
cd /d "%~dp0"

REM Verificar se o ambiente virtual existe
if not exist ".venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Falha ao criar ambiente virtual!
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado
)

REM Ativar ambiente virtual
echo [INFO] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao ativar ambiente virtual!
    pause
    exit /b 1
)

echo [OK] Ambiente virtual ativado
echo.

REM Atualizar pip
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip
echo.

REM Instalar customtkinter com verbosidade
echo ====================================================
echo [CUSTOMTKINTER] Iniciando instalação...
echo ====================================================
echo.

pip install --upgrade --verbose customtkinter

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] Houve algum aviso, mas continuaremos...
    echo.
)

echo.
echo ====================================================
echo [OK] CUSTOMTKINTER INSTALADO COM SUCESSO!
echo ====================================================
echo.

REM Verificar instalação
echo [VERIFICACAO] Testando importação...
python -c "import customtkinter; print('[OK] customtkinter versão:', customtkinter.__version__)"

if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao importar customtkinter!
    echo.
    echo Tentando instalar novamente...
    pip install --force-reinstall customtkinter
    echo.
)

echo.
echo ====================================================
echo [SUCESSO] Tudo pronto!
echo ====================================================
echo.
echo Proximos passos:
echo   1. Execute: install_dependencias.bat (para instalar tudo)
echo   2. Ou execute: INICIAR.bat (para testar a aplicacao)
echo.
pause
