@echo off
echo.
echo =========================================
echo  INSTALANDO DEPENDENCIAS - SERVIDOR
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
echo Instalando dependencias do servidor...
pip install flask
pip install flask-cors
pip install python-dateutil
pip install requests
pip install werkzeug
pip install gunicorn
pip install cryptography
echo.
echo =========================================
echo  DEPENDENCIAS INSTALADAS COM SUCESSO!
echo =========================================
echo.
echo Dependencias instaladas:
echo - Flask (servidor web)
echo - Flask-CORS (suporte cross-origin)
echo - python-dateutil (manipulacao de datas)
echo - requests (requisicoes HTTP)
echo - werkzeug (utilitarios WSGI)
echo - gunicorn (servidor de producao)
echo - cryptography (criptografia)
echo.
echo PROXIMO PASSO:
echo   Execute: INICIAR.bat
echo.
pause
