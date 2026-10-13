# Backend для проєкту

Цей бекенд забезпечує API для реєстрації, входу та управління користувачами.

## 📋 Функціонал

- ✅ Реєстрація нових користувачів
- ✅ Вхід користувачів
- ✅ Управління профілем
- ✅ Отримання списку користувачів
- ✅ Видалення облікового запису
- ✅ JWT автентифікація

## 🗄️ Структура бази даних

Користувач (`users` таблиця):
- **id** - унікальний ідентифікатор
- **login** - унікальний логін
- **password_hash** - захеширований пароль
- **email** - унікальна email адреса
- **first_name** - ім'я
- **last_name** - прізвище
- **date_of_birth** - дата народження
- **region** - регіон/країна
- **created_at** - дата створення
- **updated_at** - дата оновлення

## 🚀 Установка та запуск

### 1. Установка залежностей

```bash
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
python Backend.py
```

Сервер запуститься на: `http://localhost:8000`

## 📡 API Маршути

### Здоров'я сервера
```
GET /api/health
```

### Реєстрація
```
POST /api/register
Content-Type: application/json

{
    "login": "username",
    "password": "password123",
    "email": "user@example.com",
    "first_name": "Іван",
    "last_name": "Петренко",
    "date_of_birth": "1995-05-15",
    "region": "Ukraine"
}
```

**Відповідь (201):**
```json
{
    "message": "Реєстрація пройшла успішно",
    "user": {
        "id": 1,
        "login": "username",
        "email": "user@example.com",
        "first_name": "Іван",
        "last_name": "Петренко",
        "date_of_birth": "1995-05-15",
        "region": "Ukraine",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00"
    },
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Вхід
```
POST /api/login
Content-Type: application/json

{
    "login": "username",
    "password": "password123"
}
```

**Відповідь (200):**
```json
{
    "message": "Вхід успішний",
    "user": {...},
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Отримання профілю
```
GET /api/profile
Authorization: Bearer <token>
```

### Оновлення профілю
```
PUT /api/profile
Authorization: Bearer <token>
Content-Type: application/json

{
    "email": "newemail@example.com",
    "first_name": "Петро",
    "last_name": "Іванов",
    "region": "Kyiv",
    "date_of_birth": "1995-05-15",
    "password": "newpassword123"
}
```

### Отримання списку користувачів
```
GET /api/users
```

### Отримання інформації про користувача
```
GET /api/users/<user_id>
```

### Видалення облікового запису
```
DELETE /api/account
Authorization: Bearer <token>
```

### Надсилання повідомлення та документів у чат

```
POST /api/chat
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

Надсилайте текстове поле `message` і один або кілька файлів у повторюваних полях `files`. Для запитів без файлів, як і раніше, підтримується JSON `{ "message": "..." }`.

Підтримуються TXT, MD, CSV, JSON, PDF та DOCX. Ліміти: до 5 файлів, до 10 МБ на файл, до 20 МБ загалом і до 60 000 символів витягнутого тексту. Скановані PDF без текстового шару та зображення поки не підтримуються.

Файли не зберігаються на сервері: бекенд витягує текст у пам'яті та передає його до AI-сервісу, налаштованого через `AI_API_URL`. У базі даних зберігається лише текст повідомлення користувача без вмісту вкладень.

## 🔌 Інтеграція з фронтенд

Фронтенд додаток використовує ці API для:

1. **Реєстрація** - відправка POST запиту на `/api/register`
2. **Вхід** - відправка POST запиту на `/api/login`
3. **Профіль** - отримання даних певного користувача
4. **Управління** - оновлення та видалення даних

## 🛡️ Безпека

- Паролі хешуються за допомогою Werkzeug
- JWT токени видають на 30 днів
- CORS дозволяє запити з будь-якого джерела (налаштуйте у production)
- Унікальність логіну та email

## ⚙️ Конфігурація

Для production:
1. Змініть `SECRET_KEY` на складний набір символів
2. Встановіть `debug=False`
3. Перевірте параметри CORS
4. Використовуйте PostgreSQL замість SQLite

## 📁 Структура файлів

```
projekt - Backend/
├── Backend.py          # Основний файл бекенду
├── requirements.txt    # Залежності Python
└── README.md          # Цей файл

DataBase/
└── users.db           # SQLite база даних (утворюється автоматично)
```

## 🐛 Розв'язування проблем

**SQLAlchemy не знайдено:**
```bash
pip install Flask-SQLAlchemy
```

**Port 5000 використовується:**
Змініть `port=5000` на інший порт у Backend.py

**CORS помилки:**
Переконайтесь, що фронтенд відправляє запити на `http://localhost:8000`
