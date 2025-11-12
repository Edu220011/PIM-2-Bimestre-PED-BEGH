@echo off
echo ==============================================
echo Instalando dependencias do projeto...
echo ==============================================

:: Verificar se o Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado. Instalando via winget...
    winget install Python.Python.3
    echo Reinicie o terminal apos a instalacao do Python.
    pause
    exit /b 1
)

:: Remover ambiente virtual antigo se existir
if exist .venv (
    echo Removendo ambiente virtual antigo...
    rmdir /s /q .venv
)

:: Criar novo ambiente virtual
echo Criando novo ambiente virtual...
python -m venv .venv

:: Ativar ambiente virtual
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

:: Atualizar pip
echo Atualizando pip...
python -m pip install --upgrade pip

:: Instalar dependencias
echo Instalando dependencias Python...
if exist requirements.txt (
    echo Instalando a partir do requirements.txt...
    pip install -r requirements.txt
) else (
    echo Instalando dependencias basicas...
    pip install customtkinter==5.2.2 bcrypt==4.1.2 python-dateutil==2.8.2
)

:: Verificar se customtkinter foi instalado corretamente
echo Verificando instalacao do customtkinter...
python -c "import customtkinter; print('customtkinter instalado com sucesso!')" 2>nul
if errorlevel 1 (
    echo Erro na instalacao do customtkinter. Tentando novamente...
    pip install --upgrade customtkinter
)

:: Verificar se bcrypt foi instalado corretamente  
echo Verificando instalacao do bcrypt...
python -c "import bcrypt; print('bcrypt instalado com sucesso!')" 2>nul
if errorlevel 1 (
    echo Erro na instalacao do bcrypt. Tentando novamente...
    pip install --upgrade bcrypt
)

echo.
echo ==============================================
echo Instalando extensoes do VS Code...
echo ==============================================

:: Instalar extensoes do VS Code
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter

echo.
echo ==============================================
echo Verificando instalacoes...
echo ==============================================

:: Listar pacotes instalados
echo.
echo Pacotes Python instalados:
pip list | findstr /i "customtkinter bcrypt dateutil"

echo.
echo ==============================================
echo Instalacao concluida com sucesso!
echo ==============================================
echo.
echo SISTEMA ACADEMICO PIM - Pronto para uso!
echo.
echo Para usar o projeto:
echo 1. Ative o ambiente virtual: .venv\Scripts\activate
echo 2. Execute o projeto: python python_tk\app_gui.py
echo.
echo Ou simplesmente execute: run_app.bat
echo.
echo Deseja testar a aplicacao agora? (S/N)
set /p resposta=
if /i "%resposta%"=="S" (
    echo Iniciando aplicacao...
    python python_tk\app_gui.py
)
echo.
pause
