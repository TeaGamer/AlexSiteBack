from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import threading
from pytz import timezone
import requests
import json

# ==================== ІНІЦІАЛІЗАЦІЯ ====================

app = Flask(__name__)

# CORS налаштування
cors_origins_env = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:10000,http://localhost:8000,https://alexsite-swzo.onrender.com')
cors_origins = [origin.strip() for origin in cors_origins_env.split(',')]

print(f"✅ CORS дозволені джерела: {cors_origins}")

CORS(app, 
     resources={"*": {"origins": cors_origins}},
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"]
)

# Конфігурація БД
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
# Конвертація postgresql:// в postgresql+psycopg:// для psycopg3
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

print(f"📍 Database URL: {DATABASE_URL}")

db = SQLAlchemy(app)

# ==================== МОДЕЛІ ====================

class User(db.Model):
    """Модель користувача"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.String(20))
    region = db.Column(db.String(120), default='Ukraine')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def find_by_login(login):
        """Пошук користувача за логіном"""
        return User.query.filter_by(login=login).first()
    
    @staticmethod
    def find_by_email(email):
        """Пошук користувача за email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def find_by_id(user_id):
        """Пошук користувача за ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def create(login, email, password, first_name, last_name, date_of_birth=None, region=None):
        """Створення нового користувача"""
        password_hash = generate_password_hash(password)
        user = User(
            login=login,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            region=region or 'Ukraine'
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def update(user_id, **kwargs):
        """Оновлення користувача"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        allowed_fields = ['email', 'first_name', 'last_name', 'date_of_birth', 'region', 'password_hash']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return user
    
    @staticmethod
    def delete(user_id):
        """Видалення користувача"""
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_all():
        """Отримання всіх користувачів"""
        return User.query.order_by(User.created_at.desc()).all()
    
    def to_dict(self, include_email=True):
        """Конвертація користувача в словник"""
        result = {
            'id': self.id,
            'login': self.login,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth,
            'region': self.region,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_email:
            result['email'] = self.email
        
        return result

# ==================== МОДЕЛЬ ПОДІЙ ====================

class Event(db.Model):
    """Модель подій календаря"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    reminder = db.Column(db.Boolean, default=True)  # Чи показувати нагадування
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Конвертація події в словник"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'location': self.location,
            'reminder': self.reminder,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def create(user_id, title, start_time, end_time, description=None, location=None):
        """Створення нової події"""
        event = Event(
            user_id=user_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location
        )
        db.session.add(event)
        db.session.commit()
        return event
    
    @staticmethod
    def find_by_id(event_id):
        """Пошук події за ID"""
        return Event.query.get(event_id)
    
    @staticmethod
    def find_by_user(user_id):
        """Пошук всих подій користувача"""
        return Event.query.filter_by(user_id=user_id).order_by(Event.start_time).all()
    
    @staticmethod
    def find_upcoming(user_id, minutes=30):
        """Пошук близьких подій (за замовчуванням на 30 хв)"""
        now = datetime.utcnow()
        future = now + timedelta(minutes=minutes)
        return Event.query.filter(
            Event.user_id == user_id,
            Event.start_time >= now,
            Event.start_time <= future,
            Event.is_completed == False
        ).order_by(Event.start_time).all()
    
    @staticmethod
    def update(event_id, **kwargs):
        """Оновлення події"""
        event = Event.query.get(event_id)
        if not event:
            return None
        
        allowed_fields = ['title', 'description', 'start_time', 'end_time', 'location', 'reminder', 'is_completed']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(event, key, value)
        
        event.updated_at = datetime.utcnow()
        db.session.commit()
        return event
    
    @staticmethod
    def delete(event_id):
        """Видалення події"""
        event = Event.query.get(event_id)
        if event:
            db.session.delete(event)
            db.session.commit()
            return True
        return False

# ==================== МОДЕЛЬ ЧАТУ ====================

class ChatMessage(db.Model):
    """Модель повідомлення чату"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)  # Повідомлення користувача
    response = db.Column(db.Text, nullable=True)  # Відповідь ШІ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Конвертація повідомлення в словник"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def create(user_id, message, response=None):
        """Створення нового повідомлення"""
        chat_msg = ChatMessage(
            user_id=user_id,
            message=message,
            response=response
        )
        db.session.add(chat_msg)
        db.session.commit()
        return chat_msg
    
    @staticmethod
    def find_by_user(user_id, limit=50):
        """Отримання історії чату користувача"""
        return ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.created_at.desc()).limit(limit).all()[::-1]
    
    @staticmethod
    def find_by_id(msg_id):
        """Пошук повідомлення за ID"""
        return ChatMessage.query.get(msg_id)
    
    @staticmethod
    def update_response(msg_id, response):
        """Оновлення відповіді ШІ"""
        msg = ChatMessage.query.get(msg_id)
        if msg:
            msg.response = response
            msg.updated_at = datetime.utcnow()
            db.session.commit()
            return msg
        return None

# ==================== JWT ТОКЕНИ ====================

def generate_token(user_id):
    """Генерування JWT токена"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Перевірка JWT токена"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

def get_current_user_id(request):
    """Отримання ID поточного користувача з токена"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        print(f"❌ Authorization header відсутній або невірний формат: {auth_header}")
        return None
    
    try:
        parts = auth_header.split(' ')
        if len(parts) < 2:
            print(f"❌ Невірний формат Authorization header: {auth_header}")
            return None
        
        token = parts[1]
        user_id = verify_token(token)
        if user_id is None:
            print(f"❌ Невірний або закінчився токен")
        return user_id
    except Exception as e:
        print(f"❌ Помилка при парсингу токена: {str(e)}")
        return None

# ==================== API МАРШРУТИ ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Перевірка стану сервера"""
    return jsonify({'status': 'ok', 'message': 'Backend is running'}), 200

@app.route('/api/verify-token', methods=['GET', 'POST', 'OPTIONS'])
def verify_token_endpoint():
    """Перевірка валідності токена (DEBUG)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    
    auth_header = request.headers.get('Authorization', '')
    
    if user_id:
        return jsonify({
            'status': 'valid',
            'user_id': user_id,
            'message': 'Токен дійсний'
        }), 200
    else:
        return jsonify({
            'status': 'invalid',
            'auth_header': auth_header[:20] + '...' if len(auth_header) > 20 else auth_header,
            'message': 'Токен невірний або відсутній',
            'hint': 'Переконайтеся, що Header містить: Authorization: Bearer <TOKEN>'
        }), 401

# >>>>>>>>>> РЕЄСТРАЦІЯ >>>>>>>>>>

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    """Реєстрація нового користувача"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        required_fields = ['login', 'password', 'email', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Поле "{field}" є обов\'язковим'}), 400
        
        if User.find_by_login(data['login']):
            return jsonify({'error': 'Користувач з таким логіном вже існує'}), 409
        
        if User.find_by_email(data['email']):
            return jsonify({'error': 'Користувач з таким email вже існує'}), 409
        
        if len(data['password']) < 6:
            return jsonify({'error': 'Пароль повинен мати мінімум 6 символів'}), 400
        
        user = User.create(
            login=data['login'],
            password=data['password'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=data.get('date_of_birth'),
            region=data.get('region', 'Ukraine')
        )
        
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Реєстрація пройшла успішно',
            'user': user.to_dict(),
            'token': token
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Помилка реєстрації: {str(e)}'}), 500

# >>>>>>>>>> ВХІД >>>>>>>>>>

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    """Вхід користувача"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data.get('login') or not data.get('password'):
            return jsonify({'error': 'Логін та пароль обов\'язкові'}), 400
        
        # Спочатку шукаємо по login, потім по email
        user = User.find_by_login(data['login'])
        if not user:
            user = User.find_by_email(data['login'])
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Невірні облікові дані'}), 401
        
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Вхід успішний',
            'user': user.to_dict(),
            'token': token
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Помилка входу: {str(e)}'}), 500

# >>>>>>>>>> ПРОФІЛЬ >>>>>>>>>>

@app.route('/api/profile', methods=['GET', 'OPTIONS'])
def get_profile():
    """Отримання профілю поточного користувача"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    user = User.find_by_id(user_id)
    if not user:
        return jsonify({'error': 'Користувача не знайдено'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@app.route('/api/profile', methods=['PUT', 'OPTIONS'])
def update_profile():
    """Оновлення профілю користувача"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    try:
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'Користувача не знайдено'}), 404
        
        data = request.get_json()
        updates = {}
        
        if 'email' in data:
            existing = User.find_by_email(data['email'])
            if existing and existing.id != user_id:
                return jsonify({'error': 'Цей email вже використовується'}), 409
            updates['email'] = data['email']
        
        if 'first_name' in data:
            updates['first_name'] = data['first_name']
        
        if 'last_name' in data:
            updates['last_name'] = data['last_name']
        
        if 'region' in data:
            updates['region'] = data['region']
        
        if 'date_of_birth' in data:
            updates['date_of_birth'] = data['date_of_birth']
        
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'error': 'Пароль повинен мати мінімум 6 символів'}), 400
            updates['password_hash'] = generate_password_hash(data['password'])
        
        updated_user = User.update(user_id, **updates)
        
        return jsonify({
            'message': 'Профіль оновлено',
            'user': updated_user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Помилка оновлення: {str(e)}'}), 500

# >>>>>>>>>> КОРИСТУВАЧІ >>>>>>>>>>

@app.route('/api/users', methods=['GET', 'OPTIONS'])
def get_users():
    """Отримання списку користувачів"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        users = User.get_all()
        return jsonify({
            'users': [user.to_dict(include_email=False) for user in users],
            'total': len(users)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Помилка отримання користувачів: {str(e)}'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET', 'OPTIONS'])
def get_user(user_id):
    """Отримання інформації про конкретного користувача"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user = User.find_by_id(user_id)
    if not user:
        return jsonify({'error': 'Користувача не знайдено'}), 404
    
    return jsonify({'user': user.to_dict(include_email=False)}), 200

# >>>>>>>>>> ВИДАЛЕННЯ ОБЛІКОВОГО ЗАПИСУ >>>>>>>>>>

@app.route('/api/account', methods=['DELETE', 'OPTIONS'])
def delete_account():
    """Видалення облікового запису"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    try:
        User.delete(user_id)
        return jsonify({'message': 'Обліковий запис видалено'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Помилка видалення: {str(e)}'}), 500

# ==================== КАЛЕНДАР / ПОДІЇ ====================

@app.route('/api/calendar/current', methods=['GET', 'OPTIONS'])
def get_calendar_current():
    """Отримання поточної дати, часу та близьких подій"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    try:
        now = datetime.utcnow()
        upcoming_events = Event.find_upcoming(user_id, minutes=30)
        
        return jsonify({
            'current_time': now.isoformat(),
            'current_date': now.date().isoformat(),
            'upcoming_events': [event.to_dict() for event in upcoming_events],
            'has_upcoming': len(upcoming_events) > 0
        }), 200
    except Exception as e:
        return jsonify({'error': f'Помилка отримання календаря: {str(e)}'}), 500

# >>>>>>>>>> СОБЫТИЯ >>>>>>>>>>

@app.route('/api/events', methods=['GET', 'OPTIONS'])
def get_events():
    """Отримання всих подій користувача"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    try:
        events = Event.find_by_user(user_id)
        return jsonify({
            'events': [event.to_dict() for event in events],
            'total': len(events)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Помилка отримання подій: {str(e)}'}), 500

@app.route('/api/events', methods=['POST', 'OPTIONS'])
def create_event():
    """Створення нової події"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    try:
        data = request.get_json()
        
        # Обов'язкові поля
        required_fields = ['title', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Поле "{field}" є обов\'язковим'}), 400
        
        # Парсинг дат
        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        except:
            return jsonify({'error': 'Невірний формат дати. Використовуйте ISO 8601'}), 400
        
        if start_time >= end_time:
            return jsonify({'error': 'Час початку повинен бути раніше часу закінчення'}), 400
        
        event = Event.create(
            user_id=user_id,
            title=data['title'],
            start_time=start_time,
            end_time=end_time,
            description=data.get('description'),
            location=data.get('location')
        )
        
        return jsonify({
            'message': 'Подія створена',
            'event': event.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Помилка створення події: {str(e)}'}), 500

@app.route('/api/events/<int:event_id>', methods=['GET', 'OPTIONS'])
def get_event(event_id):
    """Отримання конкретної події"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    event = Event.find_by_id(event_id)
    if not event:
        return jsonify({'error': 'Подію не знайдено'}), 404
    
    if event.user_id != user_id:
        return jsonify({'error': 'Немає доступу до цієї події'}), 403
    
    return jsonify({'event': event.to_dict()}), 200

@app.route('/api/events/<int:event_id>', methods=['PUT', 'OPTIONS'])
def update_event(event_id):
    """Оновлення події"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    event = Event.find_by_id(event_id)
    if not event:
        return jsonify({'error': 'Подію не знайдено'}), 404
    
    if event.user_id != user_id:
        return jsonify({'error': 'Немає доступу до цієї події'}), 403
    
    try:
        data = request.get_json()
        updates = {}
        
        if 'title' in data:
            updates['title'] = data['title']
        
        if 'description' in data:
            updates['description'] = data['description']
        
        if 'location' in data:
            updates['location'] = data['location']
        
        if 'reminder' in data:
            updates['reminder'] = data['reminder']
        
        if 'is_completed' in data:
            updates['is_completed'] = data['is_completed']
        
        if 'start_time' in data:
            try:
                updates['start_time'] = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            except:
                return jsonify({'error': 'Невірний формат дати'}), 400
        
        if 'end_time' in data:
            try:
                updates['end_time'] = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            except:
                return jsonify({'error': 'Невірний формат дати'}), 400
        
        updated_event = Event.update(event_id, **updates)
        
        return jsonify({
            'message': 'Подія оновлена',
            'event': updated_event.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Помилка оновлення: {str(e)}'}), 500

@app.route('/api/events/<int:event_id>', methods=['DELETE', 'OPTIONS'])
def delete_event(event_id):
    """Видалення події"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    event = Event.find_by_id(event_id)
    if not event:
        return jsonify({'error': 'Подію не знайдено'}), 404
    
    if event.user_id != user_id:
        return jsonify({'error': 'Немає доступу до цієї події'}), 403
    
    try:
        Event.delete(event_id)
        return jsonify({'message': 'Подія видалена'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Помилка видалення: {str(e)}'}), 500

@app.route('/api/events/upcoming/<int:minutes>', methods=['GET', 'OPTIONS'])
def get_upcoming_events(minutes):
    """Отримання близьких подій (з можливістю встановити кількість хвилин)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    try:
        if minutes <= 0 or minutes > 1440:  # Макс 24 години
            minutes = 30
        
        upcoming_events = Event.find_upcoming(user_id, minutes=minutes)
        
        return jsonify({
            'events': [event.to_dict() for event in upcoming_events],
            'total': len(upcoming_events),
            'check_window_minutes': minutes
        }), 200
    except Exception as e:
        return jsonify({'error': f'Помилка отримання подій: {str(e)}'}), 500

# ==================== ЧАТ З ШІ ====================

def call_ai_api(message, chat_history=None):
    """
    Виклик AI API для отримання відповіді.
    
    Args:
        message: Текст повідомлення від користувача
        chat_history: Історія чату для контексту (опціонально)
    
    Returns:
        Текст відповіді від ШІ або None при помилці
    """
    try:
        ai_api_url = os.environ.get('AI_API_URL', 'http://localhost:8001/api/chat/stream')
        
        # Формуємо запит
        payload = {
            'message': message
        }
        
        # Викликаємо AI API
        response = requests.post(
            ai_api_url,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ AI API помилка: {response.status_code}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Помилка при виклику AI API: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Невідома помилка: {str(e)}")
        return None

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_with_ai():
    """Чат з ШІ з зберіганням історії"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        auth_header = request.headers.get('Authorization', '')
        print(f"❌ Запит до /api/chat без валідного токена. Auth header: {auth_header[:30] if auth_header else 'відсутній'}...")
        return jsonify({
            'error': 'Не автентифіковано',
            'message': 'Токен не знайдено або він невірний. Переконайтеся, що токен передано у форматі: Authorization: Bearer <TOKEN>'
        }), 401
    
    try:
        data = request.get_json()
        
        if not data.get('message') or not data['message'].strip():
            return jsonify({'error': 'Повідомлення не може бути пустим'}), 400
        
        message = data['message'].strip()
        
        # Отримуємо історію чату для контексту
        chat_history = ChatMessage.find_by_user(user_id, limit=10)
        
        # Зберігаємо повідомлення користувача
        chat_msg = ChatMessage.create(user_id, message)
        
        # Викликаємо AI API
        ai_response = call_ai_api(message, chat_history)
        
        if ai_response is None:
            return jsonify({
                'error': 'Не вдалося отримати відповідь від ШІ',
                'message_id': chat_msg.id
            }), 503
        
        # Оновлюємо відповідь у БД
        ChatMessage.update_response(chat_msg.id, ai_response)
        
        return jsonify({
            'message_id': chat_msg.id,
            'user_message': message,
            'ai_response': ai_response,
            'timestamp': chat_msg.created_at.isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Помилка чату: {str(e)}")
        return jsonify({'error': f'Помилка чату: {str(e)}'}), 500

@app.route('/api/chat/history', methods=['GET', 'OPTIONS'])
def get_chat_history():
    """Отримання історії чату користувача"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({
            'error': 'Не автентифіковано',
            'message': 'Токен не знайдено або він невірний'
        }), 401
    
    try:
        limit = request.args.get('limit', default=50, type=int)
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 10
        
        chat_history = ChatMessage.find_by_user(user_id, limit=limit)
        
        return jsonify({
            'messages': [msg.to_dict() for msg in chat_history],
            'total': len(chat_history)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Помилка отримання історії: {str(e)}'}), 500

@app.route('/api/chat/<int:msg_id>', methods=['DELETE', 'OPTIONS'])
def delete_chat_message(msg_id):
    """Видалення повідомлення з історії"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_current_user_id(request)
    if not user_id:
        return jsonify({'error': 'Не автентифіковано'}), 401
    
    try:
        msg = ChatMessage.find_by_id(msg_id)
        if not msg:
            return jsonify({'error': 'Повідомлення не знайдено'}), 404
        
        if msg.user_id != user_id:
            return jsonify({'error': 'Немає доступу до цього повідомлення'}), 403
        
        db.session.delete(msg)
        db.session.commit()
        
        return jsonify({'message': 'Повідомлення видалено'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Помилка видалення: {str(e)}'}), 500

# ==================== ОБРОБКА ПОМИЛОК ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Маршрут не знайдено'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Помилка сервера'}), 500

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == '__main__':
    with app.app_context():
        print("🔄 Ініціалізація бази даних...")
        db.create_all()
        print("✓ База даних готова")
    
    port = int(os.environ.get('PORT', 8000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("🚀 Запуск Flask сервера...")
    print(f"📍 http://0.0.0.0:{port}")
    print("💡 Натисніть Ctrl+C для зупинки\n")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
