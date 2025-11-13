@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python python\client_gui.py
pause
