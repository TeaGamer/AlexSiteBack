# 🔐 Інструкція для фронтенду: Аутентифікація та відправлення запитів до ШІ

## Проблема
Фронтенд видає помилку "Не автентифіковано" при звернені до ШІ.

## Рішення

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

```javascript
// Після успішного входу
const response = await fetch('http://backend-url/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ login: 'user@example.com', password: 'password' })
});

const data = await response.json();
if (data.token) {
  // ✅ Збережіть токен
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('user', JSON.stringify(data.user));
}
```

### 2️⃣ Відправлення запиту до ШІ (Chat)

Коли відправляєте запит до чату, **ОБОВ'ЯЗКОВО** включіть токен у заголовок `Authorization`:

```javascript
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
  const error = await response.json();
  console.error('Помилка:', error);
}

const data = await response.json();
console.log('Відповідь:', data.ai_response);
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

```javascript
async function sendChatMessage(message) {
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
      const error = await response.json();
      console.error('❌ Помилка від сервера:', error.message);
      
      if (response.status === 401) {
        console.error('❌ Токен невірний або закінчився. Виконайте вхід заново.');
        localStorage.removeItem('auth_token');
      }
      
      return null;
    }
    
    const data = await response.json();
    console.log('✅ Відповідь від ШІ:', data.ai_response);
    return data;
    
  } catch (error) {
    console.error('❌ Помилка при відправленні:', error);
    return null;
  }
}
```

### 6️⃣ Отримання історії чату

```javascript
async function getChatHistory(limit = 50) {
  const token = localStorage.getItem('auth_token');
  
  const response = await fetch(
    `http://backend-url/api/chat/history?limit=${limit}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return await response.json();
}
```

### 7️⃣ Обробка помилки на фронтенді

```javascript
// Якщо отримуєте 401 (Not Authenticated)
if (error.status === 401) {
  alert('Сесія закінчилась. Будь ласка, увійдіть заново.');
  localStorage.removeItem('auth_token');
  window.location.href = '/login'; // Перенаправте на сторінку входу
}
```

## Контрольний список

- [ ] Токен зберігається в `localStorage` після входу
- [ ] При запиті до ШІ токен відправляється в заголовку `Authorization: Bearer TOKEN`
- [ ] Формат заголовка точно відповідає `Bearer ` (з пробілом після Bearer)
- [ ] При 401 помилці користувач перенаправляється на сторінку входу
- [ ] Токен оновлюється при кожному новому входу

## Ще потрібна допомога?

Запустіть бекенд з дебаг-логуванням та перевірте консоль:

```bash
python Backend.py
```

Дебаг-логи покажуть точну причину помилки аутентифікації.

