# Конфігурація для Backend

import os

class Config:
    """Базова конфігурація"""
    
    # База даних
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Безпека
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'local-development-key-change-before-deploy'
    
    # JWT
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '4'))
    
    # Сервер
    HOST = '0.0.0.0'
    PORT = 8000
    DEBUG = True


class DevelopmentConfig(Config):
    """Конфігурація для розробки"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Конфігурація для production"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Конфігурація для тестування"""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Вибір конфігурації
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
