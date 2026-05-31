@echo off
cd /d "%~dp0"
echo Conectando Trivago Food ao iFood...
python -m pip install -q playwright
playwright install chromium 2>nul
python conectar_ifood.py
pause
