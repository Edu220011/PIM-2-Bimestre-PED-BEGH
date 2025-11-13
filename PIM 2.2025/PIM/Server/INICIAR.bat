@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python conexao\maq1\server.py
pause
