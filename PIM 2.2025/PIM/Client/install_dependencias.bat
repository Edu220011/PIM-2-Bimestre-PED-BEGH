@echo off
set "VENV_DIR=.venv"

echo.
echo =======================================================
echo     1. CRIANDO/ATIVANDO AMBIENTE VIRTUAL
echo =======================================================
echo.

:: Verifica se o ambiente virtual ja existe
if not exist "%VENV_DIR%" (
    echo Criando ambiente virtual em %VENV_DIR%...
    python -m venv %VENV_DIR%
)

:: Ativa o ambiente virtual (para o CMD)
call "%VENV_DIR%\Scripts\activate"

echo.
echo =======================================================
echo     2. INSTALANDO DEPENDENCIAS
echo =======================================================
echo.

:: Cria o arquivo de requisitos temporario e instala as dependencias
echo Flask>requirements.txt
echo Flask-CORS>>requirements.txt
echo customtkinter>>requirements.txt
echo bcrypt>>requirements.txt
echo requests>>requirements.txt

pip install -r requirements.txt

:: Limpa
del requirements.txt

echo.
echo =======================================================
echo     ✅ INSTALAÇÃO CONCLUIDA!
echo =======================================================
echo.
echo O ambiente virtual (.venv) esta pronto para uso.
pause