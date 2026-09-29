bat
@echo off
title Цифровой мониторинг земель

cd /d "%~dp0"

echo.
echo ==========================================
echo      ЦИФРОВОЙ МОНИТОРИНГ ЗЕМЕЛЬ
echo ==========================================
echo.

if not exist "bot.py" (
    echo ОШИБКА: bot.py не найден!
    pause
    exit
)

if not exist "server.py" (
    echo ОШИБКА: server.py не найден!
    pause
    exit
)

if not exist "map.html" (
    echo ОШИБКА: map.html не найден!
    pause
    exit
)

echo Все файлы найдены.
echo.

echo [1/3] Запуск Telegram-бота...
start "Telegram Bot" cmd /k "cd /d "%~dp0" && python bot.py"

timeout /t 2 /nobreak >nul

echo [2/3] Запуск сервера...
start "Land Monitoring Server" cmd /k "cd /d "%~dp0" && python -m uvicorn server:app --host 127.0.0.1 --port 8000"

timeout /t 4 /nobreak >nul

echo [3/3] Открытие карты...
start "" "http://127.0.0.1:8000/?v=3"

echo.
echo ==========================================
echo             СИСТЕМА ЗАПУЩЕНА
echo ==========================================
echo.
echo Telegram-бот  : ЗАПУЩЕН
echo FastAPI       : ЗАПУЩЕН
echo Новая карта   : ОТКРЫТА
echo.
echo Карта:
echo http://127.0.0.1:8000/
echo.
echo ==========================================
echo.

pause


