@echo off
setlocal
chcp 65001 >nul
title Chronicles of Gemini - RPG Motoru

echo ========================================================
echo   CHRONICLES OF GEMINI - AI SANDBOX ROL YAPMA MOTORU
echo ========================================================
echo.

:: 1. Python kontrolu
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [HATA] Python bulunamadi!
        echo Lutfen Python 3 kurun ve PATH kutucugunu isaretleyin.
        echo https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    set PY_CMD=py
) else (
    set PY_CMD=python
)

:: 2. Eski asili kalmis port 5000 oturumlarini temizle
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo [BILGI] Port 5000 uzerindeki eski oturum sonlandiriliyor - PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: 3. Bagimlilik kontrolu
%PY_CMD% -c "import flask, requests" >nul 2>&1
if errorlevel 1 (
    echo [BILGI] Gerekli paketler yukleniyor - Flask ve Requests...
    %PY_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [HATA] Paketler yuklenirken bir sorun olustu.
        pause
        exit /b 1
    )
)

:: 4. Tarayiciyi baslat ve sunucuyu calistir
echo.
echo [BASARILI] Sunucu baslatiliyor: http://127.0.0.1:5000
echo [BILGI] Tarayiciniz otomatik acilacaktir...
echo Kapatmak icin bu pencereyi kapatabilir veya CTRL+C yapabilirsiniz.
echo.

start "" "http://127.0.0.1:5000"

%PY_CMD% app.py

if errorlevel 1 (
    echo.
    echo [HATA] Sunucu beklenmedik sekilde durdu!
    pause
)