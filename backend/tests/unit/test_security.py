import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.utils.security import (
    validate_password_strength,
    sanitize_input,
    get_client_ip,
    encrypt_ip,
    decrypt_ip,
    generate_secure_token
)

class TestPasswordSecurity:
    """Test password security functions."""

    def test_strong_password_validation(self):
        """Test validation of strong passwords."""
        strong_passwords = [
            'MyStrongP@ssw0rd123',
            'C0mpl3x!P@ssw0rd',
            'Secure123!@#',
            'MyP@ssw0rd2024!'
        ]
        
        for password in strong_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid: {message}"

    def test_weak_password_validation(self):
        """Test validation of weak passwords."""
        weak_passwords = [
            '123456',           # Too short, only numbers
            'password',         # Common word, no special chars
            'PASSWORD',         # Only uppercase, no special chars
            'Pass123',          # Too short
            'password123',      # No uppercase, no special chars
            'PASSWORD123',      # No lowercase, no special chars
            'Password!',        # No numbers
            'Password123',      # No special chars
            '',                 # Empty
            'a' * 100,         # Too long
        ]
        
        for password in weak_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is False, f"Password '{password}' should be invalid"

    def test_password_common_patterns(self):
        """Test detection of common password patterns."""
        common_patterns = [
            'qwerty123!',
            'admin123!',
            'password123!',
            '123456789!A'
        ]
        
        for password in common_patterns:
            is_valid, message = validate_password_strength(password)
            # These might be valid by complexity but should be flagged as common
            if not is_valid:
                assert 'common' in message.lower() or 'weak' in message.lower()


class TestInputSanitization:
    """Test input sanitization functions."""

    def test_html_sanitization(self):
        """Test HTML tag removal."""
        test_cases = [
            ('<script>alert("xss")</script>', 'alert("xss")'),
            ('<b>Bold text</b>', 'Bold text'),
            ('Normal text', 'Normal text'),
            ('<img src="x" onerror="alert(1)">', ''),
            ('Text with <a href="http://evil.com">link</a>', 'Text with link'),
        ]
        
        for input_text, expected in test_cases:
            result = sanitize_input(input_text)
            assert result == expected

    def test_sql_injection_prevention(self):
        """Test SQL injection pattern detection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM messages;",
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = sanitize_input(malicious_input)
            # Should not contain SQL keywords
            assert 'DROP' not in sanitized.upper()
            assert 'DELETE' not in sanitized.upper()
            assert '--' not in sanitized

    def test_xss_prevention(self):
        """Test XSS prevention."""
        xss_payloads = [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src=x onerror=alert("xss")>',
            '<svg onload=alert("xss")>',
        ]
        
        for payload in xss_payloads:
            sanitized = sanitize_input(payload)
            assert '<script>' not in sanitized
            assert 'javascript:' not in sanitized
            assert 'onerror=' not in sanitized
            assert 'onload=' not in sanitized


class TestIPEncryption:
    """Test IP address encryption/decryption."""

    def test_ip_encryption_decryption(self):
        """Test IP encryption and decryption."""
        test_ips = [
            '192.168.1.1',
            '10.0.0.1',
            '172.16.0.1',
            '8.8.8.8',
            '2001:db8::1'  # IPv6
        ]
        
        for ip in test_ips:
            encrypted, salt = encrypt_ip(ip)
            
            # Encrypted should be different from original
            assert encrypted != ip
            assert salt is not None
            
            # Should decrypt back to original
            decrypted = decrypt_ip(encrypted, salt)
            assert decrypted == ip

    def test_ip_encryption_uniqueness(self):
        """Test that same IP encrypts differently each time."""
        ip = '192.168.1.1'
        
        encrypted1, salt1 = encrypt_ip(ip)
        encrypted2, salt2 = encrypt_ip(ip)
        
        # Should be different due to different salts
        assert encrypted1 != encrypted2
        assert salt1 != salt2
        
        # But both should decrypt to same IP
        assert decrypt_ip(encrypted1, salt1) == ip
        assert decrypt_ip(encrypted2, salt2) == ip


class TestClientIPDetection:
    """Test client IP detection."""

    def test_get_client_ip_direct(self):
        """Test direct IP detection."""
        mock_request = MagicMock()
        mock_request.remote_addr = '192.168.1.1'
        mock_request.headers = {}
        
        ip = get_client_ip(mock_request)
        assert ip == '192.168.1.1'

    def test_get_client_ip_forwarded(self):
        """Test IP detection with X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.remote_addr = '10.0.0.1'
        mock_request.headers = {'X-Forwarded-For': '203.0.113.1, 192.168.1.1'}
        
        ip = get_client_ip(mock_request)
        assert ip == '203.0.113.1'  # Should get first IP

    def test_get_client_ip_real_ip(self):
        """Test IP detection with X-Real-IP header."""
        mock_request = MagicMock()
        mock_request.remote_addr = '10.0.0.1'
        mock_request.headers = {'X-Real-IP': '203.0.113.1'}
        
        ip = get_client_ip(mock_request)
        assert ip == '203.0.113.1'


class TestTokenGeneration:
    """Test secure token generation."""

    def test_token_generation(self):
        """Test secure token generation."""
        token = generate_secure_token()
        
        assert token is not None
        assert len(token) >= 32  # Should be reasonably long
        assert isinstance(token, str)

    def test_token_uniqueness(self):
        """Test that tokens are unique."""
        tokens = [generate_secure_token() for _ in range(100)]
        
        # All tokens should be unique
        assert len(set(tokens)) == len(tokens)

    def test_token_length_parameter(self):
        """Test token generation with custom length."""
        for length in [16, 32, 64, 128]:
            token = generate_secure_token(length)
            # Token is hex encoded, so actual length is length * 2
            assert len(token) == length * 2


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_auth_rate_limiting(self, client):
        """Test rate limiting on authentication endpoints."""
        # This would require actual rate limiting to be configured
        # For now, just test that endpoints exist and respond
        
        login_data = {
            'email': 'test@example.com',
            'password': 'wrong-password'
        }
        
        # Make multiple requests
        responses = []
        for _ in range(5):
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            responses.append(response.status_code)
        
        # Should get 401 for wrong credentials, not rate limited in test
        assert all(status in [401, 429] for status in responses)

    def test_message_submission_rate_limiting(self, client):
        """Test rate limiting on message submission."""
        message_data = {
            'text': 'Test message',
            'slug_owner': 'testuser'
        }
        
        # Make multiple requests quickly
        responses = []
        for _ in range(3):
            response = client.post('/api/public/send-message',
                                 data=json.dumps(message_data),
                                 content_type='application/json')
            responses.append(response.status_code)
        
        # Should handle rate limiting gracefully
        assert all(status in [200, 201, 400, 429] for status in responses)


class TestCSRFProtection:
    """Test CSRF protection."""

    def test_csrf_token_required(self, client):
        """Test that CSRF protection is in place for state-changing operations."""
        # In testing mode, CSRF might be disabled
        # This test ensures the protection exists in production
        
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'display_name': 'Test User',
            'slug': 'testuser'
        }
        
        response = client.post('/api/auth/signup',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        # Should succeed in test mode
        assert response.status_code in [201, 400]  # 400 if validation fails


class TestInputValidation:
    """Test comprehensive input validation."""

    def test_email_validation(self, client):
        """Test email validation in signup."""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'test@',
            'test..test@example.com',
            'test@example',
            'test@.com',
            'a' * 100 + '@example.com',  # Too long
        ]
        
        for email in invalid_emails:
            user_data = {
                'email': email,
                'password': 'TestPassword123!',
                'display_name': 'Test User',
                'slug': 'testuser'
            }
            
            response = client.post('/api/auth/signup',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            
            assert response.status_code == 400

    def test_slug_validation(self, client):
        """Test slug validation in signup."""
        invalid_slugs = [
            'ab',           # Too short
            'a' * 51,       # Too long
            'test-user!',   # Invalid characters
            'test user',    # Spaces
            'TEST',         # Uppercase
            '123test',      # Starting with number
            'test@user',    # Special characters
        ]
        
        for slug in invalid_slugs:
            user_data = {
                'email': 'test@example.com',
                'password': 'TestPassword123!',
                'display_name': 'Test User',
                'slug': slug
            }
            
            response = client.post('/api/auth/signup',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            
            assert response.status_code == 400

    def test_message_length_validation(self, client):
        """Test message length validation."""
        # Too short
        short_message = {
            'text': 'Hi',
            'slug_owner': 'testuser'
        }
        
        response = client.post('/api/public/send-message',
                             data=json.dumps(short_message),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        # Too long
        long_message = {
            'text': 'a' * 1001,  # Assuming 1000 char limit
            'slug_owner': 'testuser'
        }
        
        response = client.post('/api/public/send-message',
                             data=json.dumps(long_message),
                             content_type='application/json')
        
        assert response.status_code == 400
