import pytest
import tempfile
import os
from src.main import create_app
from src.models import db
from src.models.user import User
from src.models.message import Message
from src.models.admin import AdminUser
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'SECRET_KEY': 'test-secret-key'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'display_name': 'Test User',
        'slug': 'testuser'
    }

@pytest.fixture
def admin_data():
    """Sample admin data for testing."""
    return {
        'email': 'admin@example.com',
        'password': 'AdminPassword123!',
        'display_name': 'Admin User',
        'slug': 'adminuser'
    }

@pytest.fixture
def message_data():
    """Sample message data for testing."""
    return {
        'text': 'This is a test anonymous message',
        'slug_owner': 'testuser'
    }

@pytest.fixture
def create_user(app):
    """Factory to create test users."""
    def _create_user(**kwargs):
        with app.app_context():
            user_data = {
                'email': 'test@example.com',
                'password': 'TestPassword123!',
                'display_name': 'Test User',
                'slug': 'testuser'
            }
            user_data.update(kwargs)
            
            user = User(
                email=user_data['email'],
                display_name=user_data['display_name'],
                slug=user_data['slug']
            )
            user.set_password(user_data['password'])
            user.is_verified = True
            
            db.session.add(user)
            db.session.commit()
            return user
    return _create_user

@pytest.fixture
def create_admin(app):
    """Factory to create test admin users."""
    def _create_admin(**kwargs):
        with app.app_context():
            # First create a regular user
            user_data = {
                'email': 'admin@example.com',
                'password': 'AdminPassword123!',
                'display_name': 'Admin User',
                'slug': 'adminuser'
            }
            user_data.update(kwargs)
            
            user = User(
                email=user_data['email'],
                display_name=user_data['display_name'],
                slug=user_data['slug']
            )
            user.set_password(user_data['password'])
            user.is_verified = True
            
            db.session.add(user)
            db.session.flush()
            
            # Then create admin record
            admin = AdminUser(
                user_id=user.id,
                role=kwargs.get('role', 'admin'),
                is_active=True
            )
            
            db.session.add(admin)
            db.session.commit()
            return user, admin
    return _create_admin

@pytest.fixture
def create_message(app):
    """Factory to create test messages."""
    def _create_message(user_slug='testuser', **kwargs):
        with app.app_context():
            message_data = {
                'text': 'This is a test anonymous message',
                'slug_owner': user_slug,
                'moderation_status': 'approved'
            }
            message_data.update(kwargs)
            
            message = Message(**message_data)
            db.session.add(message)
            db.session.commit()
            return message
    return _create_message

@pytest.fixture
def auth_headers(app, create_user):
    """Create authentication headers for testing."""
    def _auth_headers(user=None, **user_kwargs):
        with app.app_context():
            if user is None:
                user = create_user(**user_kwargs)
            
            access_token = create_access_token(identity=user.id)
            return {'Authorization': f'Bearer {access_token}'}
    return _auth_headers

@pytest.fixture
def admin_headers(app, create_admin):
    """Create admin authentication headers for testing."""
    def _admin_headers(**admin_kwargs):
        with app.app_context():
            user, admin = create_admin(**admin_kwargs)
            access_token = create_access_token(identity=user.id)
            return {'Authorization': f'Bearer {access_token}'}
    return _admin_headers

@pytest.fixture
def sample_ip_data():
    """Sample IP geolocation data for testing."""
    return {
        'ip': '8.8.8.8',
        'country': 'United States',
        'region': 'California',
        'city': 'Mountain View',
        'latitude': 37.4056,
        'longitude': -122.0775,
        'confidence': 85
    }

@pytest.fixture
def mock_geoip_response():
    """Mock GeoIP response for testing."""
    return {
        'country': 'Brazil',
        'region': 'São Paulo',
        'city': 'São Paulo',
        'lat': -23.5505,
        'lon': -46.6333,
        'confidence': 90,
        'provider': 'maxmind'
    }
