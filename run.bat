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
    if errorlevel 1 (
        echo [!] Не вдалося створити віртуальне середовище
        pause
        exit /b 1
    )
    echo [✓] Віртуальне середовище створено
)

REM Активація віртуального середовища
echo [*] Активація віртуального середовища...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [!] Не вдалося активувати віртуальне середовище
    pause
    exit /b 1
)

REM Встановлення залежностей
echo [*] Встановлення залежностей...
python -m pip install -r requirements.txt

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
if not defined PORT set PORT=8000
echo [📍] http://localhost:%PORT%
echo [*] Натисніть Ctrl+C для зупинки
echo ====================================
echo.

python Backend.py

pause
