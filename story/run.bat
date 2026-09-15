@echo off
chcp 65001 > nul
title Chronicles of Gemini - RPG Motoru
echo ========================================================
echo   CHRONICLES OF GEMINI - AI SANDBOX ROL YAPMA MOTORU
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python 3 yukleyin.
    pause
    exit /b
)

echo Bagimliliklar kontrol ediliyor...
python -m pip install -r requirements.txt --quiet

echo.
echo Sunucu baslatiliyor: http://127.0.0.1:5000
echo Tarayici aciliyor...
start http://127.0.0.1:5000

python app.py
pause
