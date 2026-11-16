# Інтеграція Backend з Next.js Frontend

## 📋 Огляд

Цей документ описує, як інтегрувати Next.js фронтенд з Python Flask бекенд для роботи з користувачами.

## 🔧 Налаштування CORS

Бекенд дозволяє джерела зі змінної середовища `CORS_ORIGINS`. За замовчуванням
дозволено локальний фронтенд на `http://localhost:3000` і налаштований production-домен.

### Якщо виникають CORS помилки:

Додайте точний origin фронтенду у `.env` (без кінцевого `/`), наприклад:
```bash
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

У production `CORS_ORIGINS` за замовчуванням дозволяє лише `https://alexsite-swzo.onrender.com`;
замініть його на фактичні frontend-origin. Не використовуйте wildcard origin у production.

## 🌍 URL Бекенду

- **Розробка**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`

## 📡 Структура запитів

### 1. Реєстрація

**Запит (Frontend):**
```typescript
const handleRegister = async (data: RegisterData) => {
    const response = await fetch('http://localhost:8000/api/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            login: data.username,
            password: data.password,
            email: data.email,
            first_name: data.firstName,
            last_name: data.lastName,
            date_of_birth: data.dateOfBirth,
            region: data.region
        })
    });
    
    const result = await response.json();
    
    if (response.ok) {
        // Збереження токена
        localStorage.setItem('token', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
        // Перенаправлення на dashboard
        window.location.href = '/dashboard';
    } else {
        // Обробка помилки
        console.error(result.error);
    }
};
```

**Структура дат:**
```
date_of_birth: "1995-05-15" (формат YYYY-MM-DD)
```

### 2. Вхід

**Запит (Frontend):**
```typescript
const handleLogin = async (login: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ login, password })
    });
    
    const result = await response.json();
    
    if (response.ok) {
        localStorage.setItem('token', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
    }
};
```

### 3. Отримання Профілю

**Запит (Frontend):**
```typescript
const getProfile = async () => {
    const token = localStorage.getItem('token');
    
    const response = await fetch('http://localhost:8000/api/profile', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    
    const result = await response.json();
    return result.user;
};
```

### 4. Оновлення Профілю

**Запит (Frontend):**
```typescript
const updateProfile = async (updates: Partial<User>) => {
    const token = localStorage.getItem('token');
    
    const response = await fetch('http://localhost:8000/api/profile', {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
    });
    
    return await response.json();
};
```

### 5. Видалення Облікового Запису

**Запит (Frontend):**
```typescript
const deleteAccount = async () => {
    const token = localStorage.getItem('token');
    
    const response = await fetch('http://localhost:8000/api/account', {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (response.ok) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
    }
};
```

## 🔐 Управління Токенами

### Збереження токена
```typescript
localStorage.setItem('token', response.token);
```

### Використання токена в запитах
```typescript
headers: {
    'Authorization': `Bearer ${token}`
}
```

### Отримання токена
```typescript
const token = localStorage.getItem('token');
```

### Видалення токена (вихід)
```typescript
const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
};
```

## ⚠️ Обробка Помилок

### Коди Статусу

- `200` - OK
- `201` - Created (успішна реєстрація)
- `400` - Bad Request (неправильні дані)
- `401` - Unauthorized (не автентифіковано)
- `409` - Conflict (користувач вже існує)
- `500` - Server Error

### Приклад обробки:

```typescript
const handleRequest = async (url: string, options: RequestInit) => {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (response.status === 401) {
            // Токен виліків або невірний
            localStorage.removeItem('token');
            window.location.href = '/login';
        } else if (!response.ok) {
            throw new Error(data.error || 'Unknown error');
        }
        
        return data;
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
};
```

## 📦 Типи TypeScript

```typescript
interface User {
    id: number;
    login: string;
    email: string;
    first_name: string;
    last_name: string;
    date_of_birth: string | null;
    region: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

interface AuthResponse {
    message: string;
    user: User;
    token: string;
}

interface ErrorResponse {
    error: string;
}
```

## 🚀 API Service Wrapper

Рекомендується створити service для всіх API запитів:

```typescript
// services/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiService = {
    async register(data: RegisterData) {
        const response = await fetch(`${API_BASE}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async login(login: string, password: string) {
        const response = await fetch(`${API_BASE}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ login, password })
        });
        return response.json();
    },
    
    async getProfile() {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/api/profile`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response.json();
    },
    
    // ... інші методи
};
```

## 🐛 Розв'язування Проблем

### "Failed to fetch" помилка
- Переконайтесь, що бекенд запущено на `http://localhost:8000`
- Перевірте, чи порт 8000 не блокується фаєрволом

### CORS помилка при запиті
- Додайте CORS headers у запит
- Перевірте конфігурацію Flask-CORS

### Токен недійсний
- Перевірте, чи токен зберігається правильно
- Токен може мати строк дії (30 днів за замовчуванням)
- Пересиліть користувача для нового токена

## 📚 Подальша інтеграція

- [ ] Додати refresh token
- [ ] Реалізувати reset пароля
- [ ] Додати 2FA
- [ ] Реалізувати rate limiting
- [ ] Додати логування всіх дій користувача
