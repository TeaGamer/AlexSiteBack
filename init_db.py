# Скрипт ініціалізації та насичення бази даних

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Додаємо шлях до Backend.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Backend import app, User, init_db


def seed_database():
    """Додавання тестових даних"""
    print("🗑️  Видалення старих даних...")
    
    # Очистимо таблицю
    import sqlite3
    db = sqlite3.connect(app.config['DATABASE'])
    cursor = db.cursor()
    cursor.execute('DELETE FROM users')
    db.commit()
    db.close()
    
    print("✓ Таблиця очищена")
    
    # Тестові користувачі
    test_users = [
        {
            'login': 'ivan_petrov',
            'password': 'Password123',
            'email': 'ivan.petrov@example.com',
            'first_name': 'Іван',
            'last_name': 'Петров',
            'date_of_birth': '1995-05-15',
            'region': 'Kyiv, Ukraine'
        },
        {
            'login': 'maria_kovalenko',
            'password': 'SecurePass456',
            'email': 'maria.kovalenko@example.com',
            'first_name': 'Марія',
            'last_name': 'Коваленко',
            'date_of_birth': '1998-08-22',
            'region': 'Lviv, Ukraine'
        },
        {
            'login': 'oleh_mykhailov',
            'password': 'MyPass789!',
            'email': 'oleh.mykhailov@example.com',
            'first_name': 'Олег',
            'last_name': 'Михайлов',
            'date_of_birth': '1992-03-10',
            'region': 'Kharkiv, Ukraine'
        },
        {
            'login': 'natalia_shevchenko',
            'password': 'NatPass321#',
            'email': 'natalia.shevchenko@example.com',
            'first_name': 'Наталія',
            'last_name': 'Шевченко',
            'date_of_birth': '2000-01-25',
            'region': 'Odesa, Ukraine'
        },
    ]
    
    for user_data in test_users:
        user = User.create(**user_data)
        print(f"✓ Додано користувача: {user['login']}")
    
    print(f"\n✅ Додано {len(test_users)} тестових користувачів")


def drop_database():
    """Видалення всіх таблиць"""
    print("⚠️  Видалення всіх таблиць...")
    response = input("Ви впевнені? (yes/no): ").strip().lower()
    
    if response == 'yes':
        import sqlite3
        db = sqlite3.connect(app.config['DATABASE'])
        cursor = db.cursor()
        cursor.execute('DROP TABLE IF EXISTS users')
        db.commit()
        db.close()
        print("✓ Все таблиці видалені")
    else:
        print("❌ Операція скасована")


def list_users():
    """Вивід списку всіх користувачів"""
    users = User.get_all()
    
    if not users:
        print("❌ Немає користувачів у базі даних")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<5} {'Login':<20} {'Email':<30} {'Ім\'я':<15} {'Регіон':<15}")
    print("="*80)
    
    for user in users:
        full_name = f"{user['first_name']} {user['last_name']}"
        print(f"{user['id']:<5} {user['login']:<20} {user['email']:<30} {full_name:<15} {user['region'] or 'N/A':<15}")
    
    print("="*80)
    print(f"Всього: {len(users)} користувачів\n")


def get_user_stats():
    """Статистика користувачів"""
    users = User.get_all()
    
    print("\n📊 Статистика Бази Даних")
    print(f"Всього користувачів: {len(users)}")
    
    if len(users) > 0:
        # Сортуємо за created_at
        sorted_users = sorted(users, key=lambda x: x['created_at'])
        oldest_user = sorted_users[0]
        newest_user = sorted_users[-1]
        
def main():
    """Головна функція"""
    print("\n" + "="*60)
    print("   Database Management Script")
    print("="*60 + "\n")
    
    commands = {
        '1': ('Ініціалізація бази даних', init_db),
        '2': ('Додавання тестових даних', seed_database),
        '3': ('Видалення всіх таблиць', drop_database),
        '4': ('Вивід списку користувачів', list_users),
        '5': ('Статистика бази даних', get_user_stats),
        '0': ('Вихід', None)
    }
    
    for key, (description, _) in commands.items():
        print(f"[{key}] {description}")
    
    print("\n" + "-"*60)
    choice = input("Виберіть опцію (0-5): ").strip()
    
    if choice == '0':
        print("До побачення! 👋")
        return
    
    if choice not in commands:
        print("❌ Невірна опція")
        return
    
    description, func = commands[choice]
    print(f"\n▶️  {description}...")
    
    if func:
        try:
            func()
            print("✓ Операція завершена успішно\n")
        except Exception as e:
            print(f"❌ Помилка: {str(e)}\n")


if __name__ == '__main__':
    main()
