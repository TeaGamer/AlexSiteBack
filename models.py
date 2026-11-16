# Моделі бази даних

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


def utcnow():
    """Return a naive UTC timestamp for compatibility with existing database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    """Модель користувача"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    region = db.Column(db.String(120), nullable=True)  # країна/регіон
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    
    def __repr__(self):
        return f'<User {self.login}>'
    
    def set_password(self, password):
        """Хешування пароля"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Перевірка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_email=True):
        """Конвертація в словник"""
        data = {
            'id': self.id,
            'login': self.login,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'region': self.region,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_email:
            data['email'] = self.email
        
        return data
    
    @classmethod
    def find_by_login(cls, login):
        """Пошук користувача за логіном"""
        return cls.query.filter_by(login=login).first()
    
    @classmethod
    def find_by_email(cls, email):
        """Пошук користувача за email"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        """Пошук користувача за ID"""
        return cls.query.get(user_id)
    
    def get_full_name(self):
        """Отримання повного імені"""
        return f"{self.first_name} {self.last_name}"
    
    def update_last_login(self):
        """Оновлення часу останнього входу"""
        self.updated_at = utcnow()
        db.session.commit()
