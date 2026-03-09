from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# ==================== ІНІЦІАЛІЗАЦІЯ ====================

app = Flask(__name__)

# CORS налаштування
cors_origins_env = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000')
cors_origins = [origin.strip() for origin in cors_origins_env.split(',')]

print(f"✅ CORS дозволені джерела: {cors_origins}")

CORS(app, 
     resources={"*": {"origins": cors_origins}},
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"]
)

# Конфігурація БД
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/alexsite')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

print(f"📍 Database URL: {DATABASE_URL}")

# ==================== ДОПОМІЖНІ ФУНКЦІЇ БД ====================

def get_db():
    """Отримання з'єднання з базою даних"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Помилка з'єднання з БД: {e}")
        raise

def init_db():
    """Ініціалізація бази даних"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                login TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT,
                region TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✓ Таблиця users готова")
    except Exception as e:
        print(f"❌ Помилка ініціалізації БД: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# ==================== МОДЕЛІ ====================

class User:
    @staticmethod
    def find_by_login(login):
        """Пошук користувача за логіном"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('SELECT * FROM users WHERE login = %s', (login,))
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def find_by_email(email):
        """Пошук користувача за email"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def find_by_id(user_id):
        """Пошук користувача за ID"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def create(login, email, password, first_name, last_name, date_of_birth=None, region=None):
        """Створення нового користувача"""
        conn = get_db()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (login, email, password_hash, first_name, last_name, date_of_birth, region)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (login, email, password_hash, first_name, last_name, date_of_birth, region or 'Ukraine'))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            return User.find_by_id(user_id)
        except psycopg2.IntegrityError as e:
            conn.rollback()
            raise Exception(str(e))
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update(user_id, **kwargs):
        """Оновлення користувача"""
        conn = get_db()
        cursor = conn.cursor()
        
        allowed_fields = ['email', 'first_name', 'last_name', 'date_of_birth', 'region', 'password_hash']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            conn.close()
            return User.find_by_id(user_id)
        
        try:
            set_clause = ', '.join([f'{k} = %s' for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            
            cursor.execute(f'UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s', values)
            conn.commit()
            return User.find_by_id(user_id)
        except psycopg2.IntegrityError as e:
            conn.rollback()
            raise Exception(str(e))
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete(user_id):
        """Видалення користувача"""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_all():
        """Отримання всіх користувачів"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            users = [dict(row) for row in cursor.fetchall()]
            return users
        finally:
            cursor.close()
            conn.close()

def user_to_dict(user, include_email=True):
    """Конвертація користувача в словник"""
    if not user:
        return None
    
    result = {
        'id': user['id'],
        'login': user['login'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'date_of_birth': user['date_of_birth'],
        'region': user['region'],
        'is_active': user['is_active'],
        'created_at': user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else user['created_at'],
        'updated_at': user['updated_at'].isoformat() if isinstance(user['updated_at'], datetime) else user['updated_at']
    }
    
    if include_email:
        result['email'] = user['email']
    
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
        
        token = generate_token(user['id'])
        
        return jsonify({
            'message': 'Реєстрація пройшла успішно',
            'user': user_to_dict(user),
            'token': token
        }), 201
    
    except Exception as e:
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
        
        if not user or not check_password_hash(user['password_hash'], data['password']):
            return jsonify({'error': 'Невірні облікові дані'}), 401
        
        token = generate_token(user['id'])
        
        return jsonify({
            'message': 'Вхід успішний',
            'user': user_to_dict(user),
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
    
    return jsonify({'user': user_to_dict(user)}), 200

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
            if existing and existing['id'] != user_id:
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
            'user': user_to_dict(updated_user)
        }), 200
    
    except Exception as e:
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
            'users': [user_to_dict(u, include_email=False) for u in users],
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
    
    return jsonify({'user': user_to_dict(user, include_email=False)}), 200

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
    print("🔄 Ініціалізація бази даних...")
    init_db()
    print("✓ База даних готова")
    
    port = int(os.environ.get('PORT', 8000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("🚀 Запуск Flask сервера...")
    print(f"📍 http://0.0.0.0:{port}")
    print("💡 Натисніть Ctrl+C для зупинки\n")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
