@echo off
cd /d "%~dp0"
title Trivago Food - Servidor
color 0A

echo ========================================
echo   TRIVAGO FOOD
echo ========================================
echo.

powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:5000/api/ping' -UseBasicParsing -TimeoutSec 2).StatusCode | Out-Null; Start-Process 'http://127.0.0.1:5000'; Write-Host 'Servidor ja rodando. Abrindo navegador...'; exit 0 } catch { exit 1 }"
if %errorlevel%==0 (
    timeout /t 2 /nobreak >nul
    exit /b 0
)

echo [1/3] Instalando dependencias...
python -m pip install -q flask flask-cors mysql-connector-python python-dotenv openai
if errorlevel 1 (
    echo.
    echo ERRO: Python nao encontrado.
    echo Instale em https://www.python.org/downloads/
    echo Marque "Add Python to PATH" na instalacao.
    pause
    exit /b 1
)

echo [2/3] Preparando arquivos...
python copy_logo.py 2>nul

echo [3/3] Subindo servidor...
echo.
echo NAO feche esta janela enquanto usar o site.
echo O navegador abrira sozinho quando o servidor estiver pronto.
echo.

python IA_Trivago_Food.py

echo.
echo Servidor encerrado.
pause
