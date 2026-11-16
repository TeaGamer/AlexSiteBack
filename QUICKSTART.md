# 🚀 Швидкий Старт

Цей гайд допоможе вам швидко запустити проєкт.

## ⚙️ Системні Вимоги

- **Python 3.8+** - Встановіть з https://www.python.org/
- **pip** - Менеджер пакетів Python (встановлюється з Python)
- **Node.js 16+** - Для Next.js фронтенду (опціонально)

## 📦 Встановлення на Windows

### Крок 1: Встановлення залежностей

```bash
cd "c:\Users\User\Desktop\Języki i paradygmaty programowania\projekt - Backend"
pip install -r requirements.txt
```

### Крок 2: Запуск бекенду

**Варіант А: Простий запуск**
```bash
python Backend.py
```

**Варіант B: Через батник (рекомендується)**
```bash
run.bat
```

Сервер запуститься на: **http://localhost:8000**

### Крок 3: Ініціалізація бази даних

Відкрийте новий термінал та запустіть:
```bash
python init_db.py
```

Виберіть опцію:
- `1` - Ініціалізація бази даних
- `2` - Додавання тестових користувачів
- `4` - Вивід списку користувачів

### Крок 4: Перевірка роботи

Відкрийте браузер і перейдіть на:
```
http://localhost:8000/api/health
```

Має відобразитися:
```json
{
    "status": "ok",
    "message": "Backend is running"
}
```

## 📊 Тестові Користувачі

ПІСЛЯ того як додали тестові дані через `init_db.py`, можна використовувати:

| Login | Password | Email |
|-------|----------|-------|
| ivan_petrov | Password123 | ivan.petrov@example.com |
| maria_kovalenko | SecurePass456 | maria.kovalenko@example.com |
| oleh_mykhailov | MyPass789! | oleh.mykhailov@example.com |
| natalia_shevchenko | NatPass321# | natalia.shevchenko@example.com |

## 🧪 Тестування API

### Через curl (Windows PowerShell)

**Реєстрація:**
```powershell
$body = @{
    login = "testuser"
    password = "TestPass123."
    email = "test@example.com"
    first_name = "Тест"
    last_name = "Користувач"
    region = "Ukraine"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/register" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body
```

**Вхід:**
```powershell
$body = @{
    login = "testuser"
    password = "TestPass123."
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/login" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body
```

### Через Postman

1. Завачте Postman: https://www.postman.com/
2. Створіть нову POST колекцію
3. Адреса: `http://localhost:8000/api/register`
4. Body (JSON):
```json
{
    "login": "newuser",
    "password": "Password123.",
    "email": "newuser@example.com",
    "first_name": "Ім'я",
    "last_name": "Прізвище",
    "date_of_birth": "1995-05-15",
    "region": "Ukraine"
}
```

## 📁 Структура Файлів

```
projekt - Backend/
├── Backend.py              # Основний файл бекенду
├── models.py               # Моделі бази даних
├── utils.py                # Допоміжні функції
├── config.py               # Конфігурація
├── init_db.py              # Скрипт ініціалізації БД
├── requirements.txt        # Python залежності
├── run.bat                 # Скрипт запуску (Windows)
├── run.sh                  # Скрипт запуску (Linux/Mac)
├── README.md               # Детальна документація
├── INTEGRATION.md          # інструкція інтеграції з фронтенд
├── QUICKSTART.md          # Цей файл
├── .env.example            # Шаблон змінних середовища
└── .gitignore              # Git ignore файл

DataBase/
└── users.db                # SQLite база даних (утворюється автоматично)
```

## 🔧 Розв'язування Проблем

### "ModuleNotFoundError: No module named 'flask'"

```bash
pip install Flask
pip install -r requirements.txt
```

### "The port 8000 is in use"

Змініть порт у Backend.py:
```python
app.run(debug=True, host='0.0.0.0', port=8001)  # Змініть 8000 на 8001
```

### База даних не створюється

Переконайтесь, що папка `DataBase` існує:
```bash
mkdir ..\DataBase
```

### CORS помилка від фронтенду

Перевірте, чи URL бекенду правильно встановлено у фронтенді:
```javascript
const API_BASE = 'http://localhost:8000';
```

## 🚀 Наступні Кроки

1. **Frontend**: Запустіть Next.js додаток
   ```bash
   cd Проєкт/alexsite
   npm install
   npm run dev
   ```
   Буде доступний на: http://localhost:3000

2. **Тестування**: Протестуйте реєстрацію та вхід через фронтенд

3. **Production**: Дивіться [README.md](README.md) для розгортання

## 📚 Додаткова Документація

- [README.md](README.md) - Повна документація
- [INTEGRATION.md](INTEGRATION.md) - Інтеграція з фронтенд
- [Backend.py](Backend.py) - Код аппа з коментарями

## 🆘 Допомога

Якщо виникають проблеми:

1. Перевірте логи консолі (там будуть помилки)
2. Переконайтесь, що всі залежності встановлені
3. Спробуйте перезапустити сервер
4. Дивіться розділ "Розв'язування Проблем" у README.md

## ✅ Контрольний Список

- [ ] Python 3.8+ встановлено
- [ ] requirements.txt встановлено
- [ ] Backend запущено на localhost:8000
- [ ] Тестові користувачі додані
- [ ] API /api/health відповідає
- [ ] База даних створена
- [ ] Готово до інтеграції з фронтенд

Успїхи! 🎉
