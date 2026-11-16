import os
import unittest
from datetime import datetime
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, patch

os.environ['FLASK_ENV'] = 'testing'

from Backend import ChatMessage, Event, User, app, call_ai_api, db
import init_db as database_manager
from sqlalchemy import inspect


class BackendApiTests(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        self.addCleanup(self.app_context.pop)
        self.addCleanup(db.session.remove)
        self.client = app.test_client()

    def register_user(self):
        response = self.client.post('/api/register', json={
            'login': 'testuser',
            'password': 'StrongPass123.',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        token = response.get_json()['token']
        return {'Authorization': f'Bearer {token}'}

    def test_invalid_json_returns_client_error(self):
        response = self.client.post(
            '/api/login',
            data='{',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_database_management_commands(self):
        with redirect_stdout(StringIO()):
            database_manager.init_db()
            database_manager.seed_database()
        self.assertEqual(User.query.count(), 4)

        with patch('builtins.input', return_value='yes'), redirect_stdout(StringIO()):
            database_manager.drop_database()
        self.assertEqual(inspect(db.engine).get_table_names(), [])

        database_manager.init_db()
        self.assertIn('users', inspect(db.engine).get_table_names())

    def test_event_dates_are_normalized_and_validated(self):
        headers = self.register_user()
        response = self.client.post('/api/events', headers=headers, json={
            'title': 'Event',
            'start_time': '2030-01-01T13:00:00+03:00',
            'end_time': '2030-01-01T14:00:00+03:00',
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        event = response.get_json()['event']
        self.assertEqual(event['start_time'], '2030-01-01T10:00:00')

        response = self.client.put(
            f"/api/events/{event['id']}",
            headers=headers,
            json={'end_time': '2029-01-01T10:00:00Z'},
        )
        self.assertEqual(response.status_code, 400)

    def test_account_deletion_removes_owned_data(self):
        headers = self.register_user()
        user = User.find_by_login('testuser')
        Event.create(
            user.id,
            'Event',
            start_time=datetime(2030, 1, 1),
            end_time=datetime(2030, 1, 2),
        )
        ChatMessage.create(user.id, 'question', 'answer')

        response = self.client.delete('/api/account', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(Event.query.count(), 0)
        self.assertEqual(ChatMessage.query.count(), 0)

    def test_ai_request_includes_previous_conversation(self):
        user = User.create(
            login='testuser',
            email='test@example.com',
            password='StrongPass123.',
            first_name='Test',
            last_name='User',
        )
        history = [ChatMessage.create(user.id, 'prior question', 'prior answer')]
        response = Mock(status_code=200, text='response')

        with patch('Backend.requests.post', return_value=response) as post:
            result = call_ai_api('new question', history)

        self.assertEqual(result, 'response')
        prompt = post.call_args.kwargs['json']['message']
        self.assertIn('prior question', prompt)
        self.assertIn('prior answer', prompt)
        self.assertIn('new question', prompt)


if __name__ == '__main__':
    unittest.main()
