from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

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
        return None
    
    token = auth_header.split(' ')[1]
    return verify_token(token)

# ==================== API МАРШРУТИ ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Перевірка стану сервера"""
    return jsonify({'status': 'ok', 'message': 'Backend is running'}), 200

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
