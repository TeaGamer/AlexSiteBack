#!/bin/bash

# Скрипт для запуску Backend на Linux/Mac

echo "===================================="
echo "   Backend Startup Script"
echo "===================================="
echo ""

# Перевірка Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 не встановлено!"
    echo "Будь ласка, встановіть Python 3"
    exit 1
fi

echo "[✓] Python знайдено: $(python3 --version)"

# Перевірка та створення віртуального середовища
if [ ! -d "venv" ]; then
    echo "[*] Створення віртуального середовища..."
    python3 -m venv venv
    echo "[✓] Віртуальне середовище створено"
fi

# Активація віртуального середовища
echo "[*] Активація віртуального середовища..."
source venv/bin/activate

# Встановлення залежностей
echo "[*] Встановлення залежностей..."
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "[!] Помилка при встановленні залежностей"
    exit 1
fi

echo "[✓] Залежності встановлені"

# Запуск сервера
echo ""
echo "===================================="
echo "[*] Запуск Flask сервера..."
echo "[📍] http://localhost:8000"
echo "[*] Натисніть Ctrl+C для зупинки"
echo "===================================="
echo ""

python Backend.py
