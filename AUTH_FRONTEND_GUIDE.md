# 🔐 Інструкція для фронтенду: Аутентифікація та відправлення запитів до ШІ

## Проблема
Фронтенд видає помилку "Не автентифіковано" при звернені до ШІ.

## Рішення

### 🚀 Початок (Initialization)

**TypeScript версія:**

```typescript
// 1. Визначте типи
interface User {
  id: number;
  login: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
}

interface AuthService {
  token: string | null;
  user: User | null;
  
  setToken(token: string): void;
  getToken(): string | null;
  clearAuth(): void;
  isAuthenticated(): boolean;
}

// 2. Створіть Auth Service
const authService: AuthService = {
  token: localStorage.getItem('auth_token'),
  user: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')!) : null,
  
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('auth_token', token);
  },
  
  getToken(): string | null {
    return this.token || localStorage.getItem('auth_token');
  },
  
  clearAuth(): void {
    this.token = null;
    this.user = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },
  
  isAuthenticated(): boolean {
    return !!this.getToken();
  }
};

// 3. Експортуйте для використання в компонентах
export default authService;
```

### 1️⃣ Після входу користувача (Login)

Після успішного входу, бекенд повертає:

```json
{
  "message": "Вхід успішний",
  "user": { ... },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Важливо:** Збережіть токен у `localStorage`:

**TypeScript версія:**

```typescript
interface LoginResponse {
  message: string;
  user: {
    id: number;
    login: string;
    email: string;
    first_name: string;
    last_name: string;
    created_at: string;
  };
  token: string;
}

// Після успішного входу
const response = await fetch('http://backend-url/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ login: 'user@example.com', password: 'Password123.' })
});

const data: LoginResponse = await response.json();
if (data.token) {
  // ✅ Збережіть токен
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('user', JSON.stringify(data.user));
}
```

### 2️⃣ Відправлення запиту до ШІ (Chat)

Коли відправляєте запит до чату, **ОБОВ'ЯЗКОВО** включіть токен у заголовок `Authorization`:

**TypeScript версія:**

```typescript
interface ChatResponse {
  message_id: number;
  user_message: string;
  ai_response: string;
  timestamp: string;
}

interface ChatError {
  error: string;
  message: string;
  message_id?: number;
}

const token = localStorage.getItem('auth_token');

const response = await fetch('http://backend-url/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`  // ✅ ВАЖЛИВО!
  },
  body: JSON.stringify({ message: 'Привіт!' })
});

if (!response.ok) {
  const error: ChatError = await response.json();
  console.error('Помилка:', error.message);
} else {
  const data: ChatResponse = await response.json();
  console.log('Відповідь:', data.ai_response);
}
```

### 3️⃣ Формат заголовка Authorization

Заголовок **ПОВИНЕН** мати точний формат:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

❌ **Неправильно:**
- `Authorization: your_token`
- `Authorization: Token your_token`
- `Authorization: Bearer`
- `Bearer your_token`

✅ **Правильно:**
- `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 4️⃣ Перевірка токена (DEBUG)

Щоб перевірити, чи токен відправляється правильно, зробіть запит до:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://backend-url/api/verify-token
```

**Успішна відповідь (200):**
```json
{
  "status": "valid",
  "user_id": 123,
  "message": "Токен дійсний"
}
```

**Помилка (401):**
```json
{
  "status": "invalid",
  "auth_header": "відсутній або невірний",
  "message": "Токен невірний або відсутній",
  "hint": "Переконайтеся, що Header містить: Authorization: Bearer <TOKEN>"
}
```

### 5️⃣ Повна функція для чату

**TypeScript версія:**

```typescript
interface ChatMessage {
  message_id: number;
  user_message: string;
  ai_response: string;
  timestamp: string;
}

interface ChatErrorResponse {
  error: string;
  message: string;
}

async function sendChatMessage(message: string): Promise<ChatMessage | null> {
  try {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      console.error('❌ Токен не знайдено. Спочатку виконайте вхід.');
      return null;
    }
    
    const response = await fetch('http://backend-url/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message })
    });
    
    if (!response.ok) {
      const error: ChatErrorResponse = await response.json();
      console.error('❌ Помилка від сервера:', error.message);
      
      if (response.status === 401) {
        console.error('❌ Токен невірний або закінчився. Виконайте вхід заново.');
        localStorage.removeItem('auth_token');
      }
      
      return null;
    }
    
    const data: ChatMessage = await response.json();
    console.log('✅ Відповідь від ШІ:', data.ai_response);
    return data;
    
  } catch (error) {
    console.error('❌ Помилка при відправленні:', error);
    return null;
  }
}

// Використання
const response = await sendChatMessage('Як ти робиш?');
if (response) {
  console.log(`ID повідомлення: ${response.message_id}`);
  console.log(`Мій запит: ${response.user_message}`);
  console.log(`Відповідь ШІ: ${response.ai_response}`);
}
```

### 6️⃣ Отримання історії чату

**TypeScript версія:**

```typescript
interface ChatHistoryItem {
  id: number;
  user_id: number;
  message: string;
  response: string | null;
  created_at: string;
  updated_at: string;
}

interface ChatHistoryResponse {
  total: number;
  messages: ChatHistoryItem[];
}

async function getChatHistory(limit: number = 50): Promise<ChatHistoryResponse | null> {
  try {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      console.error('❌ Токен не знайдено');
      return null;
    }
    
    const response = await fetch(
      `http://backend-url/api/chat/history?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (!response.ok) {
      console.error('❌ Помилка отримання історії:', response.status);
      return null;
    }
    
    const data: ChatHistoryResponse = await response.json();
    return data;
    
  } catch (error) {
    console.error('❌ Помилка при отриманні історії:', error);
    return null;
  }
}

// Використання
const history = await getChatHistory(10);
if (history) {
  history.messages.forEach(msg => {
    console.log(`Ви: ${msg.message}`);
    console.log(`ШІ: ${msg.response}`);
  });
}
```

### 7️⃣ Обробка помилки на фронтенді

**TypeScript версія:**

```typescript
type ErrorCode = 400 | 401 | 403 | 404 | 500 | 503;

interface ApiError {
  error: string;
  message?: string;
  status: ErrorCode;
}

async function handleAuthError(error: ApiError): Promise<void> {
  switch (error.status) {
    case 401:
      console.error('❌ Сесія закінчилась. Виконайте вхід заново.');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login'; // Перенаправте на сторінку входу
      break;
      
    case 403:
      console.error('❌ Доступ заборонено');
      break;
      
    case 404:
      console.error('❌ Ресурс не знайдено');
      break;
      
    case 500:
      console.error('❌ Помилка сервера:', error.message);
      break;
      
    case 503:
      console.error('❌ Сервіс недоступний (ШІ API проблема)');
      break;
      
    default:
      console.error('❌ Невідома помилка:', error.message);
  }
}

// Використання
try {
  const response = await fetch('http://backend-url/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
    },
    body: JSON.stringify({ message: 'Test' })
  });
  
  if (!response.ok) {
    const error = await response.json();
    await handleAuthError({
      ...error,
      status: response.status as ErrorCode
    });
  }
} catch (error) {
  console.error('Network error:', error);
}
```

## Контрольний список

- [ ] Токен зберігається в `localStorage` після входу
- [ ] При запиті до ШІ токен відправляється в заголовку `Authorization: Bearer TOKEN`
- [ ] Формат заголовка точно відповідає `Bearer ` (з пробілом після Bearer)
- [ ] При 401 помилці користувач перенаправляється на сторінку входу
- [ ] Токен оновлюється при кожному новому входу

## 📦 Альтернатива: Использование Axios

Якщо ви використовуєте **Axios** (часто простіше за Fetch):

**TypeScript версія:**

```typescript
import axios, { AxiosInstance } from 'axios';

interface ApiClient {
  get<T>(url: string): Promise<T>;
  post<T>(url: string, data: any): Promise<T>;
}

const apiClient: AxiosInstance = axios.create({
  baseURL: 'http://backend-url'
});

// Додайте Interceptor для автоматичного додавання токена
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обробка 401 помилок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Тепер можна просто:
async function sendMessage(message: string): Promise<ChatResponse | null> {
  try {
    const response = await apiClient.post<ChatResponse>('/api/chat', { message });
    return response.data;
  } catch (error) {
    console.error('❌ Помилка:', error);
    return null;
  }
}
```

**Установка Axios:**
```bash
npm install axios
# або
yarn add axios
```

## Ще потрібна допомога?

Запустіть бекенд з дебаг-логуванням та перевірте консоль:

```bash
python Backend.py
```

Дебаг-логи покажуть точну причину помилки аутентифікації.
