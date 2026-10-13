# Конфігурація для Backend

import os
from datetime import timedelta

class Config:
    """Базова конфігурація"""
    
    # База даних
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DataBase", "users.db"))}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Безпека
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # JWT
    JWT_EXPIRATION_HOURS = 24 * 30  # 30 днів
    
    # Сервер
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True


class DevelopmentConfig(Config):
    """Конфігурація для розробки"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Конфігурація для production"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Обов'язково встановіти
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Обов'язково встановіти


class TestingConfig(Config):
    """Конфігурація для тестування"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Вибір конфігурації
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
