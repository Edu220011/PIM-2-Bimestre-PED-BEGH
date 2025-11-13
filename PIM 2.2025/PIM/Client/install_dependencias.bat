@echo off
echo.
echo =========================================
echo  INSTALANDO DEPENDENCIAS - CLIENTE
echo =========================================
echo.
echo Criando ambiente virtual...
python -m venv .venv
echo.
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat
echo.
echo Atualizando pip...
python -m pip install --upgrade pip
echo.
echo Instalando dependencias do cliente...
pip install customtkinter
pip install bcrypt
pip install flask
pip install flask-cors
pip install requests
pip install python-dateutil
pip install pillow
pip install cryptography
echo.
echo =========================================
echo  DEPENDENCIAS INSTALADAS COM SUCESSO!
echo =========================================
echo.
echo Dependencias instaladas:
echo - customtkinter (interface grafica)
echo - bcrypt (autenticacao)
echo - flask (cliente HTTP)
echo - flask-cors (suporte cross-origin)
echo - requests (requisicoes HTTP)
echo - python-dateutil (manipulacao de datas)
echo - pillow (processamento de imagens)
echo - cryptography (criptografia)
echo.
echo PROXIMO PASSO:
echo   Execute: INICIAR.bat
echo.
pause
