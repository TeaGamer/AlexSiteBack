@echo off
REM Скрипт для запуску Backend на Windows

echo ====================================
echo   Backend Startup Script
echo ====================================
echo.

REM Перевірка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не встановлено!
    echo Будь ласка, встановіть Python з https://www.python.org/
    pause
    exit /b 1
)

echo [✓] Python знайдено

REM Перевірка та створення віртуального середовища
if not exist "venv" (
    echo [*] Створення віртуального середовища...
    python -m venv venv
    echo [✓] Віртуальне середовище створено
)

REM Активація віртуального середовища
echo [*] Активація віртуального середовища...
call venv\Scripts\activate.bat

REM Встановлення залежностей
echo [*] Встановлення залежностей...
pip install -r requirements.txt >nul 2>&1

if %errorlevel% neq 0 (
    echo [!] Помилка при встановленні залежностей
    pause
    exit /b 1
)

echo [✓] Залежності встановлені

REM Запуск сервера
echo.
echo ====================================
echo [*] Запуск Flask сервера...
echo [📍] http://localhost:8000
echo [*] Натисніть Ctrl+C для зупинки
echo ====================================
echo.

python Backend.py

pause
