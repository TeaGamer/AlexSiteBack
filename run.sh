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
    if ! python3 -m venv venv; then
        echo "[!] Не вдалося створити віртуальне середовище"
        exit 1
    fi
    echo "[✓] Віртуальне середовище створено"
fi

# Активація віртуального середовища
echo "[*] Активація віртуального середовища..."
if ! source venv/bin/activate; then
    echo "[!] Не вдалося активувати віртуальне середовище"
    exit 1
fi

# Встановлення залежностей
echo "[*] Встановлення залежностей..."
if ! python -m pip install -r requirements.txt; then
    echo "[!] Помилка при встановленні залежностей"
    exit 1
fi

echo "[✓] Залежності встановлені"

# Запуск сервера
echo ""
echo "===================================="
echo "[*] Запуск Flask сервера..."
echo "[📍] http://localhost:${PORT:-8000}"
echo "[*] Натисніть Ctrl+C для зупинки"
echo "===================================="
echo ""

python Backend.py
