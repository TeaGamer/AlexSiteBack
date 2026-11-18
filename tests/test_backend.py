import os
import json
import unittest
from datetime import datetime, timedelta
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, patch

os.environ['FLASK_ENV'] = 'testing'

import Backend as backend_module
from Backend import ChatMessage, Event, User, app, call_ai_api, db, utcnow
import init_db as database_manager
from sqlalchemy import inspect, text


class BackendApiTests(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        backend_module._user_schema_checked = False
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

    def test_profile_saves_and_validates_timezone(self):
        registration = self.client.post('/api/register', json={
            'login': 'timezoneuser',
            'password': 'StrongPass123.',
            'email': 'timezone@example.com',
            'first_name': 'Timezone',
            'region': 'Poland',
            'timezone_name': 'Europe/Warsaw',
        })
        self.assertEqual(registration.status_code, 201, registration.get_json())
        self.assertEqual(registration.get_json()['user']['timezone_name'], 'Europe/Warsaw')
        headers = {'Authorization': f"Bearer {registration.get_json()['token']}"}

        updated = self.client.put('/api/profile', headers=headers, json={
            'region': 'United States',
            'timezone_name': 'America/New_York',
        })
        self.assertEqual(updated.status_code, 200, updated.get_json())
        self.assertEqual(updated.get_json()['user']['region'], 'United States')
        self.assertEqual(updated.get_json()['user']['timezone_name'], 'America/New_York')

        invalid = self.client.put('/api/profile', headers=headers, json={
            'timezone_name': 'Mars/Olympus',
        })
        self.assertEqual(invalid.status_code, 400)

    def test_user_schema_migrates_timezone_column(self):
        db.drop_all()
        with db.engine.begin() as connection:
            connection.execute(text(
                'CREATE TABLE users ('
                'id INTEGER PRIMARY KEY, login VARCHAR(120), password_hash VARCHAR(255), '
                'email VARCHAR(120), first_name VARCHAR(120), last_name VARCHAR(120), '
                'date_of_birth VARCHAR(20), region VARCHAR(120), is_active BOOLEAN, '
                'created_at TIMESTAMP, updated_at TIMESTAMP)'
            ))
            connection.execute(text(
                "INSERT INTO users (id, login, password_hash, email, first_name, last_name, region) "
                "VALUES (1, 'legacy', 'hash', 'legacy@example.com', 'Legacy', 'User', 'Kyiv')"
            ))
            connection.execute(text(
                "INSERT INTO users (id, login, password_hash, email, first_name, last_name, region) "
                "VALUES (2, 'unset-region', 'hash', 'unset@example.com', 'Unset', 'Region', ' -- none -- ')"
            ))
        backend_module._user_schema_checked = False

        backend_module.ensure_user_profile_schema()

        columns = {column['name'] for column in inspect(db.engine).get_columns('users')}
        self.assertIn('timezone_name', columns)
        legacy_user = db.session.execute(text(
            'SELECT region, timezone_name FROM users WHERE id = 1'
        )).one()
        self.assertEqual(legacy_user.region, 'Ukraine')
        self.assertEqual(legacy_user.timezone_name, 'Europe/Kyiv')
        default_user = db.session.execute(text(
            'SELECT region, timezone_name FROM users WHERE id = 2'
        )).one()
        self.assertEqual(default_user.region, 'Poland')
        self.assertEqual(default_user.timezone_name, 'Europe/Warsaw')

    def test_registration_defaults_to_poland_and_warsaw(self):
        response = self.client.post('/api/register', json={
            'login': 'defaultregion',
            'password': 'StrongPass123.',
            'email': 'default@example.com',
            'first_name': 'Default',
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()['user']['region'], 'Poland')
        self.assertEqual(response.get_json()['user']['timezone_name'], 'Europe/Warsaw')

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

    def test_calendar_schema_migrates_existing_event_tables(self):
        db.drop_all()
        with db.engine.begin() as connection:
            connection.execute(text(
                'CREATE TABLE events ('
                'id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, title VARCHAR(255) NOT NULL, '
                'description TEXT, start_time TIMESTAMP NOT NULL, end_time TIMESTAMP NOT NULL, '
                'location VARCHAR(255), reminder BOOLEAN, is_completed BOOLEAN, '
                'created_at TIMESTAMP, updated_at TIMESTAMP)'
            ))
        backend_module._calendar_schema_checked = False

        backend_module.ensure_calendar_schema()

        columns = {column['name'] for column in inspect(db.engine).get_columns('events')}
        self.assertTrue({'category', 'is_all_day', 'deleted_at', 'legacy_id'} <= columns)
        self.assertTrue(inspect(db.engine).has_index('events', 'uq_events_user_legacy_id'))

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

    def test_event_deletion_is_recoverable_for_twelve_hours(self):
        headers = self.register_user()
        user = User.find_by_login('testuser')
        event = Event.create(
            user.id,
            'Recoverable event',
            start_time=datetime(2030, 1, 1, 10),
            end_time=datetime(2030, 1, 1, 11),
        )

        deleted = self.client.delete(f'/api/events/{event.id}', headers=headers)
        self.assertEqual(deleted.status_code, 200, deleted.get_json())
        self.assertIsNotNone(deleted.get_json()['event']['deleted_at'])
        self.assertEqual(self.client.get('/api/events', headers=headers).get_json()['total'], 0)
        self.assertEqual(self.client.get('/api/events/deleted', headers=headers).get_json()['total'], 1)

        restored = self.client.post(f'/api/events/{event.id}/restore', headers=headers)
        self.assertEqual(restored.status_code, 200, restored.get_json())
        self.assertIsNone(restored.get_json()['event']['deleted_at'])
        self.assertEqual(self.client.get('/api/events', headers=headers).get_json()['total'], 1)

    def test_expired_deleted_events_are_permanently_purged(self):
        headers = self.register_user()
        user = User.find_by_login('testuser')
        event = Event.create(
            user.id,
            'Expired event',
            start_time=datetime(2030, 1, 1, 10),
            end_time=datetime(2030, 1, 1, 11),
        )
        event_id = event.id
        event.deleted_at = utcnow() - timedelta(hours=12, seconds=1)
        db.session.commit()

        response = self.client.get('/api/events/deleted', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['total'], 0)
        self.assertIsNone(Event.find_by_id(event_id))

    def test_local_calendar_import_is_idempotent(self):
        headers = self.register_user()
        payload = {
            'timezone_offset_minutes': 0,
            'timezone_name': 'America/New_York',
            'notes': [{
                'id': 42,
                'text': 'Imported note',
                'date': '2030-01-03',
                'time': '',
                'category': 'Notes',
            }],
        }

        first = self.client.post('/api/events/import-local', headers=headers, json=payload)
        second = self.client.post('/api/events/import-local', headers=headers, json=payload)
        self.assertEqual(first.status_code, 200, first.get_json())
        self.assertEqual(first.get_json()['imported'], 1)
        self.assertEqual(second.get_json()['imported'], 0)
        event = self.client.get('/api/events', headers=headers).get_json()['events'][0]
        self.assertTrue(event['is_all_day'])
        self.assertEqual(event['category'], 'Notes')
        self.assertEqual(event['start_time'], '2030-01-03T05:00:00')

    def test_ai_calendar_actions_create_update_and_request_delete_confirmation(self):
        headers = self.register_user()

        def ai_response(action):
            return Mock(status_code=200, json=lambda: {'response': json.dumps(action)})

        with patch('Backend.requests.post', return_value=ai_response({
            'action': 'create',
            'title': 'Study session',
            'date': '2030-01-04',
            'time': '09:30',
            'category': 'Meetings',
            'description': None,
            'all_day': False,
        })):
            created = self.client.post(
                '/api/chat/parse-event',
                headers=headers,
                json={'text': 'Add a study session on January 4 at 9:30'},
            )
        self.assertEqual(created.status_code, 200, created.get_json())
        self.assertEqual(created.get_json()['action'], 'created')
        event_id = created.get_json()['event']['id']

        with patch('Backend.requests.post', return_value=ai_response({
            'action': 'update',
            'event_id': event_id,
            'title': 'Exam preparation',
            'date': None,
            'time': None,
            'category': None,
            'description': None,
            'all_day': None,
        })):
            updated = self.client.post(
                '/api/chat/parse-event',
                headers=headers,
                json={'text': 'Rename the study session to exam preparation'},
            )
        self.assertEqual(updated.status_code, 200, updated.get_json())
        self.assertEqual(updated.get_json()['action'], 'updated')
        self.assertEqual(updated.get_json()['event']['title'], 'Exam preparation')

        with patch('Backend.requests.post', return_value=ai_response({
            'action': 'delete',
            'event_id': event_id,
        })):
            pending_delete = self.client.post(
                '/api/chat/parse-event',
                headers=headers,
                json={'text': 'Delete exam preparation'},
            )
        self.assertEqual(pending_delete.status_code, 200, pending_delete.get_json())
        self.assertEqual(pending_delete.get_json()['action'], 'delete_confirmation')
        self.assertIsNone(Event.find_by_id(event_id).deleted_at)

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
