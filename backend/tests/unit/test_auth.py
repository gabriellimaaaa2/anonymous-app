import pytest
import json
from src.models.user import User
from src.models import db

class TestAuthRoutes:
    """Test authentication routes."""

    def test_signup_success(self, client, user_data):
        """Test successful user signup."""
        response = client.post('/api/auth/signup', 
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        assert 'user' in data
        assert data['user']['email'] == user_data['email']
        assert data['user']['slug'] == user_data['slug']

    def test_signup_duplicate_email(self, client, create_user, user_data):
        """Test signup with duplicate email."""
        create_user(email=user_data['email'])
        
        response = client.post('/api/auth/signup',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_signup_duplicate_slug(self, client, create_user, user_data):
        """Test signup with duplicate slug."""
        create_user(slug=user_data['slug'])
        
        response = client.post('/api/auth/signup',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_signup_invalid_email(self, client, user_data):
        """Test signup with invalid email."""
        user_data['email'] = 'invalid-email'
        
        response = client.post('/api/auth/signup',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_signup_weak_password(self, client, user_data):
        """Test signup with weak password."""
        user_data['password'] = '123'
        
        response = client.post('/api/auth/signup',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_login_success(self, client, create_user, user_data):
        """Test successful login."""
        create_user(**user_data)
        
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'user' in data

    def test_login_invalid_credentials(self, client, create_user, user_data):
        """Test login with invalid credentials."""
        create_user(**user_data)
        
        login_data = {
            'email': user_data['email'],
            'password': 'wrong-password'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401

    def test_login_unverified_user(self, client, create_user, user_data):
        """Test login with unverified user."""
        user = create_user(**user_data)
        user.is_verified = False
        db.session.commit()
        
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401

    def test_login_banned_user(self, client, create_user, user_data):
        """Test login with banned user."""
        user = create_user(**user_data)
        user.is_banned = True
        db.session.commit()
        
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 403

    def test_forgot_password_success(self, client, create_user, user_data):
        """Test successful forgot password request."""
        create_user(**user_data)
        
        forgot_data = {'email': user_data['email']}
        
        response = client.post('/api/auth/forgot-password',
                             data=json.dumps(forgot_data),
                             content_type='application/json')
        
        assert response.status_code == 200

    def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with nonexistent email."""
        forgot_data = {'email': 'nonexistent@example.com'}
        
        response = client.post('/api/auth/forgot-password',
                             data=json.dumps(forgot_data),
                             content_type='application/json')
        
        # Should still return 200 for security reasons
        assert response.status_code == 200

    def test_profile_access_with_token(self, client, auth_headers):
        """Test accessing profile with valid token."""
        headers = auth_headers()
        
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data

    def test_profile_access_without_token(self, client):
        """Test accessing profile without token."""
        response = client.get('/api/auth/profile')
        
        assert response.status_code == 401

    def test_profile_access_with_invalid_token(self, client):
        """Test accessing profile with invalid token."""
        headers = {'Authorization': 'Bearer invalid-token'}
        
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 422  # JWT decode error


class TestUserModel:
    """Test User model functionality."""

    def test_password_hashing(self, app, user_data):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(
                email=user_data['email'],
                display_name=user_data['display_name'],
                slug=user_data['slug']
            )
            user.set_password(user_data['password'])
            
            # Password should be hashed
            assert user.password_hash != user_data['password']
            
            # Should verify correct password
            assert user.check_password(user_data['password']) is True
            
            # Should not verify incorrect password
            assert user.check_password('wrong-password') is False

    def test_slug_generation(self, app):
        """Test automatic slug generation."""
        with app.app_context():
            user = User(
                email='test@example.com',
                display_name='Test User'
            )
            user.generate_slug()
            
            assert user.slug is not None
            assert len(user.slug) >= 6

    def test_user_to_dict(self, app, create_user, user_data):
        """Test user serialization."""
        with app.app_context():
            user = create_user(**user_data)
            user_dict = user.to_dict()
            
            assert user_dict['email'] == user_data['email']
            assert user_dict['display_name'] == user_data['display_name']
            assert user_dict['slug'] == user_data['slug']
            assert 'password_hash' not in user_dict
            assert 'created_at' in user_dict

    def test_user_to_dict_include_private(self, app, create_user, user_data):
        """Test user serialization with private fields."""
        with app.app_context():
            user = create_user(**user_data)
            user_dict = user.to_dict(include_private=True)
            
            assert 'is_verified' in user_dict
            assert 'is_banned' in user_dict
            assert 'reveal_credits' in user_dict
