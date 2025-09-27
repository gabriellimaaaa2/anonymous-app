import hashlib
import hmac
import secrets
import base64
from cryptography.fernet import Fernet
from flask import current_app

def hash_ip(ip_address):
    """Gera hash HMAC-SHA256 do IP usando chave secreta"""
    if not ip_address:
        return None
    
    secret = current_app.config.get('HMAC_SECRET', 'default-secret')
    return hmac.new(
        secret.encode('utf-8'),
        ip_address.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def encrypt_ip(ip_address):
    """Encripta o IP para armazenamento seguro"""
    if not ip_address:
        return None, None
    
    # Gerar salt único
    salt = secrets.token_hex(16)
    
    # Criar chave de encriptação baseada no salt e chave secreta
    secret = current_app.config.get('HMAC_SECRET', 'default-secret')
    key_material = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt.encode(), 100000)
    key = base64.urlsafe_b64encode(key_material[:32])
    
    # Encriptar IP
    fernet = Fernet(key)
    encrypted_ip = fernet.encrypt(ip_address.encode('utf-8')).decode('utf-8')
    
    return encrypted_ip, salt

def decrypt_ip(encrypted_ip, salt):
    """Decripta o IP (apenas para uso administrativo autorizado)"""
    if not encrypted_ip or not salt:
        return None
    
    try:
        # Recriar chave de encriptação
        secret = current_app.config.get('HMAC_SECRET', 'default-secret')
        key_material = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt.encode(), 100000)
        key = base64.urlsafe_b64encode(key_material[:32])
        
        # Decriptar IP
        fernet = Fernet(key)
        decrypted_ip = fernet.decrypt(encrypted_ip.encode('utf-8')).decode('utf-8')
        
        return decrypted_ip
    except Exception:
        return None

def generate_secure_token(length=32):
    """Gera token seguro para verificações"""
    return secrets.token_urlsafe(length)

def generate_api_key():
    """Gera chave de API segura"""
    return f"anm_{secrets.token_urlsafe(32)}"

def validate_password_strength(password):
    """Valida força da senha"""
    if len(password) < 10:
        return False, "Senha deve ter pelo menos 10 caracteres"
    
    checks = [
        (any(c.isupper() for c in password), "Deve conter pelo menos uma letra maiúscula"),
        (any(c.islower() for c in password), "Deve conter pelo menos uma letra minúscula"),
        (any(c.isdigit() for c in password), "Deve conter pelo menos um número"),
        (any(not c.isalnum() for c in password), "Deve conter pelo menos um símbolo")
    ]
    
    for check, message in checks:
        if not check:
            return False, message
    
    return True, "Senha válida"

def sanitize_user_input(text):
    """Sanitiza entrada do usuário"""
    if not text:
        return ""
    
    # Remover caracteres de controle
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Limitar tamanho
    return sanitized[:5000]  # Máximo 5000 caracteres

def is_safe_redirect_url(url, allowed_hosts=None):
    """Verifica se URL de redirecionamento é segura"""
    if not url:
        return False
    
    # URLs relativas são seguras
    if url.startswith('/') and not url.startswith('//'):
        return True
    
    # Verificar hosts permitidos
    if allowed_hosts:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc in allowed_hosts
    
    return False

def generate_csrf_token():
    """Gera token CSRF"""
    return secrets.token_urlsafe(32)

def verify_csrf_token(token, session_token):
    """Verifica token CSRF"""
    return secrets.compare_digest(token, session_token)

class RateLimitExceeded(Exception):
    """Exceção para rate limit excedido"""
    pass

def check_rate_limit(key, limit, window, storage=None):
    """Verifica rate limit simples (implementação básica)"""
    # TODO: Implementar com Redis para produção
    # Por enquanto, sempre permitir
    return True

def get_client_ip(request):
    """Obtém IP real do cliente considerando proxies"""
    # Verificar headers de proxy
    forwarded_ips = request.headers.get('X-Forwarded-For')
    if forwarded_ips:
        # Pegar o primeiro IP (cliente original)
        return forwarded_ips.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr

def mask_sensitive_data(data, fields_to_mask=None):
    """Mascara dados sensíveis para logs"""
    if fields_to_mask is None:
        fields_to_mask = ['password', 'token', 'secret', 'key', 'ip']
    
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(field in key.lower() for field in fields_to_mask):
                masked[key] = '***MASKED***'
            elif isinstance(value, (dict, list)):
                masked[key] = mask_sensitive_data(value, fields_to_mask)
            else:
                masked[key] = value
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item, fields_to_mask) for item in data]
    else:
        return data
