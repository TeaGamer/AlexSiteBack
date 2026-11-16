# Утиліти для Backend

import logging
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timezone
import os


def utcnow():
    """Return a naive UTC timestamp for compatibility with existing responses."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ==================== ЛОГУВАННЯ ====================

def setup_logger(name, log_file='backend.log'):
    """Налаштування логування"""
    
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


# ==================== ДЕКОРАТОРИ ====================

def validate_json(*required_fields):
    """Декоратор для валідації JSON запиту"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type має бути application/json'}), 400
            
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify({'error': 'Тіло запиту має бути JSON-об’єктом'}), 400
            
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'Поле "{field}" обов\'язкове'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_request(logger):
    """Декоратор для логування запитів"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.info(f'{request.method} {request.path} - IP: {request.remote_addr}')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== ВАЛІДАЦІЯ ====================

def is_valid_email(email):
    """Перевірка валідності email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_date(date_string):
    """Перевірка валідності дати"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def is_strong_password(password):
    """Перевірка надійності пароля"""
    if len(password) < 8:
        return False, "Пароль повинен мати мінімум 8 символів"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Пароль повинен містити великі й малі літери та цифри"
    
    return True, "Пароль достатньо надійний"


# ==================== ВІДПОВІДІ ====================

def success_response(data, message='Success', status_code=200):
    """Стандартна успішна відповідь"""
    return jsonify({
        'status': 'success',
        'message': message,
        'data': data,
        'timestamp': utcnow().isoformat()
    }), status_code


def error_response(error, status_code=400):
    """Стандартна відповідь помилки"""
    return jsonify({
        'status': 'error',
        'error': error,
        'timestamp': utcnow().isoformat()
    }), status_code


# ==================== ПАГІНАЦІЯ ====================

def paginate_query(query, page=1, per_page=20):
    """Пагінація запиту"""
    page = max(1, int(page))
    per_page = min(100, max(1, int(per_page)))
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return {
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }
