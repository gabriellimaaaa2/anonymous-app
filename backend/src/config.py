import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Configurações de email
    MAIL_SERVER = os.environ.get('SMTP_HOST') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('SMTP_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('SMTP_USER')
    MAIL_PASSWORD = os.environ.get('SMTP_PASS')
    MAIL_DEFAULT_SENDER = os.environ.get('SMTP_FROM') or 'noreply@anonimou.app'
    
    # Configurações de segurança
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS') or 12)
    HMAC_SECRET = os.environ.get('HMAC_SECRET') or 'hmac-secret-for-ip-hashing'
    
    # Configurações de rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATE_LIMIT_SEND_MESSAGE_PER_HOUR = int(os.environ.get('RATE_LIMIT_SEND_MESSAGE_PER_HOUR') or 5)
    RATE_LIMIT_SEND_MESSAGE_PER_DAY = int(os.environ.get('RATE_LIMIT_SEND_MESSAGE_PER_DAY') or 20)
    RATE_LIMIT_SEND_MESSAGE_PER_SLUG_HOUR = int(os.environ.get('RATE_LIMIT_SEND_MESSAGE_PER_SLUG_HOUR') or 10)
    
    # Configurações de pagamento
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Configurações PIX
    GERENCIANET_CLIENT_ID = os.environ.get('GERENCIANET_CLIENT_ID')
    GERENCIANET_CLIENT_SECRET = os.environ.get('GERENCIANET_CLIENT_SECRET')
    GERENCIANET_SANDBOX = os.environ.get('GERENCIANET_SANDBOX', 'true').lower() == 'true'
    GERENCIANET_PIX_KEY = os.environ.get('GERENCIANET_PIX_KEY')
    
    # Configurações GeoIP
    MAXMIND_LICENSE_KEY = os.environ.get('MAXMIND_LICENSE_KEY')
    MAXMIND_DB_PATH = os.environ.get('MAXMIND_DB_PATH') or '/tmp/GeoLite2-City.mmdb'
    IPINFO_TOKEN = os.environ.get('IPINFO_TOKEN')
    
    # Configurações de moderação
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    PERSPECTIVE_API_KEY = os.environ.get('PERSPECTIVE_API_KEY')
    
    # Configurações da aplicação
    APP_NAME = os.environ.get('APP_NAME') or 'ANONYMOUS'
    APP_URL = os.environ.get('APP_URL') or 'http://localhost:3000'
    API_URL = os.environ.get('API_URL') or 'http://localhost:5000'
    APP_DOMAIN = os.environ.get('APP_DOMAIN') or 'anonimou.app'
    
    # Configurações de preços (em centavos)
    REVEAL_PRICE_CENTS = int(os.environ.get('REVEAL_PRICE_CENTS') or 500)  # R$ 5,00
    MONTHLY_SUBSCRIPTION_CENTS = int(os.environ.get('MONTHLY_SUBSCRIPTION_CENTS') or 2499)  # R$ 24,99
    REVEAL_PACK_5_CENTS = int(os.environ.get('REVEAL_PACK_5_CENTS') or 1990)  # R$ 19,90
    
    # Configurações de upload
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    
    # Configurações de monitoramento
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    # Configurações de admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@anonimou.app'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'AdminSecure!123'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
