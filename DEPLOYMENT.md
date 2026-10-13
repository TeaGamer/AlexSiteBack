# 🌐 Розгортання (Deployment) на Production

Цей гайд описує, як розгорнути Backend на production.

## 🏗️ Варіанти Розгортання

### Варіант 1: Heroku (Найпростіший)

#### Крок 1: Встановлення Heroku CLI
```bash
# Windows
choco install heroku-cli

# Або завантажити з https://devcenter.heroku.com/articles/heroku-cli
```

#### Крок 2: Логін до Heroku
```bash
heroku login
```

#### Крок 3: Створення Procfile
Створіть файл `Procfile` в кореневій папці Backend:
```
web: gunicorn Backend:app
```

#### Крок 4: Оновлення requirements.txt
```bash
echo gunicorn==21.2.0 >> requirements.txt
echo python-dotenv==1.0.0 >> requirements.txt
```

#### Крок 5: Ініціалізація Git репозиторію
```bash
git init
git add .
git commit -m "Initial commit"
```

#### Крок 6: Создание та розгортання Heroku додатку
```bash
heroku create your-app-name
git push heroku main
```

#### Крок 7: Встановлення змінних середовища
```bash
heroku config:set SECRET_KEY="your-super-secret-key"
heroku config:set DATABASE_URL="postgresql://..."  # Якщо використовуєте PostgreSQL
```

#### Крок 8: Ініціалізація Бази Даних
```bash
heroku run python init_db.py
```

Ваш додаток буде доступний на: `https://your-app-name.herokuapp.com`

---

### Варіант 2: Railway.app (Рекомендується)

1. Перейдіть на https://railway.app
2. Натисніть "Deploy Now"
3. Виберіть GitHub репозиторій
4. Railway автоматичною розпізнає Python проєкт
5. Встановіть змінні середовища в налаштуваннях

---

### Варіант 3: AWS EC2 (Просунуте)

#### Крок 1: Запуск EC2 інстансу
- Виберіть Ubuntu 22.04 LTS
- t2.micro (Free Tier)
- Відкрийте порти 80, 443, 5000, 22

#### Крок 2: SSH доступ
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

#### Крок 3: Встановлення залежностей
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx
pip3 install -r requirements.txt
pip3 install gunicorn
```

#### Крок 4: Створення systemd служби
Створіть `/etc/systemd/system/backend.service`:
```ini
[Unit]
Description=Backend Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/projekt-backend
ExecStart=/usr/bin/python3 /home/ubuntu/projekt-backend/Backend.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Крок 5: Запуск служби
```bash
sudo systemctl daemon-reload
sudo systemctl start backend
sudo systemctl enable backend
```

---

## 📦 Production конфігурація

### 1. Оновіть конфіг

[config.py](config.py) - змініть:
```python
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # ОБОВ'ЯЗКОВО встановите
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
```

### 2. Використовуйте PostgreSQL замість SQLite

```bash
# Встановлення
pip install psycopg2-binary

# Конфігурація
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
```

### 3. Дозвільні CORS

В Backend.py:
```python
CORS(app, resources={
    "*": {
        "origins": ["https://yourdomain.com", "https://www.yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 4. Встановіть SSL сертифікат

Для HTTPS (Let's Encrypt):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com
```

## 🔒 Змінні Середовища (Production)

Встановіть на сервері:

```bash
# Безпека
export FLASK_ENV=production
export SECRET_KEY="very-long-random-string-here"

# База даних (PostgreSQL)
export DATABASE_URL="postgresql://user:pass@db.example.com:5432/mydb"

# Сервер
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"
```

## 📊 Рекомендована архітектура Production

```
┌─────────────────┐
│  Your Domain    │
│  (yourdomain.   │
│   com)          │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│   Nginx         │
│   Reverse Proxy │
│   Port 80/443   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gunicorn       │
│  Flask App      │
│  Port 5000      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  Database       │
└─────────────────┘
```

## 🚀 Запуск Production сервера з Gunicorn

```bash
# Простий запуск
gunicorn Backend:app

# З більшою кількістю workers
gunicorn -w 4 -b 0.0.0.0:5000 Backend:app

# З автоперезагрузкою при змінах
gunicorn --reload Backend:app
```

## ⚙️ Nginx конфігурація

Файл: `/etc/nginx/sites-available/backend`

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активуйте:
```bash
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 📝 Моніторинг та Логування

### Логування в файл

В config.py вже налаштовано логування в `/logs/backend.log`

### Моніторинг процесів

```bash
# Перегляд логів Systemd
sudo journalctl -u backend -f

# Перегляд процесів
ps aux | grep Backend

# Перевірка портів
netstat -tulpn | grep LISTEN
```

## 🔄 CI/CD з GitHub Actions

Створіть `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Server
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
      run: |
        mkdir -p ~/.ssh
        echo "$DEPLOY_KEY" > ~/.ssh/deploy_key
        chmod 600 ~/.ssh/deploy_key
        ssh -i ~/.ssh/deploy_key user@server "cd /app && git pull && pip install -r requirements.txt && systemctl restart backend"
```

## ✅ Production Контрольний Список

- [ ] Змінено SECRET_KEY на складну комбінацію
- [ ] Використовується PostgreSQL база даних
- [ ] CORS налаштовано для вашого домену
- [ ] SSL сертифікат встановлено
- [ ] Nginx налаштовано як reverse proxy
- [ ] Gunicorn запущено з кількома workers
- [ ] Логування налаштовано
- [ ] Регулярні резервні копії бази даних
- [ ] Встановлено мініторинг
- [ ] Готово до запуску 🎉

## 🆘 Розв'язування Проблем Production

### 502 Bad Gateway
- Перевірте, чи Gunicorn запущено
- Переконайтесь, що сокет Nginx має доступ до Gunicorn

### БД з'єднання відмовлено
- Перевірте DATABASE_URL
- Переконайтесь, що БД сервер доступний
- Перевірте firewall правила

### Поідхідна середовища сповільнює додаток
- Отримайте більше ресурсів з хостера
- Добавте caching (Redis)
- Оптимізуйте SQL запити

## 📞 Підтримка Хостингу

- **Heroku**: https://devcenter.heroku.com/
- **Railway**: https://docs.railway.app/
- **AWS**: https://docs.aws.amazon.com/
- **DigitalOcean**: https://docs.digitalocean.com/
