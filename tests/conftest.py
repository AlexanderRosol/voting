import os
import sys
import pytest
from passlib.hash import bcrypt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.app import create_app, db  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture
def app():
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'JWT_ACCESS_TOKEN_EXPIRES': False,
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_a(app):
    with app.app_context():
        user = User(
            username='alice',
            email='alice@example.com',
            password=bcrypt.hash('alicepw123')
        )
        db.session.add(user)
        db.session.commit()
        return {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'password': 'alicepw123'
        }


@pytest.fixture
def user_b(app):
    with app.app_context():
        user = User(
            username='bob',
            email='bob@example.com',
            password=bcrypt.hash('bobpw123456')
        )
        db.session.add(user)
        db.session.commit()
        return {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'password': 'bobpw123456'
        }


def _login(client, username, password):
    response = client.post('/auth/token', json={'username': username, 'password': password})
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()['access_token']


@pytest.fixture
def token_a(client, user_a):
    return _login(client, user_a['username'], user_a['password'])


@pytest.fixture
def token_b(client, user_b):
    return _login(client, user_b['username'], user_b['password'])


@pytest.fixture
def auth_header_a(token_a):
    return {'Authorization': f'Bearer {token_a}'}


@pytest.fixture
def auth_header_b(token_b):
    return {'Authorization': f'Bearer {token_b}'}
