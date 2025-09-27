import os
import sys
from datetime import datetime

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flasgger import Swagger

# Importar configurações
from src.config import config
from src.models import init_db
from src.utils.email import init_mail
from src.utils.security import get_client_ip

# Importar blueprints
from src.routes.auth import auth_bp
from src.routes.user import user_bp

def create_app(config_name='development'):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Carregar configuração
    app.config.from_object(config[config_name])
    
    # Configurar Sentry para monitoramento (se configurado)
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )
    
    # Configurar CORS
    CORS(app, origins=[
        app.config.get("APP_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ])

    # Configurar Swagger/OpenAPI
    from flasgger import Swagger
    Swagger(app, config={
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,  # Todas as rotas
                "model_filter": lambda tag: True,  # Todos os modelos
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/swagger-ui/"
    })
    
    # Inicializar extensões
    db = init_db(app)
    jwt = JWTManager(app)
    mail = init_mail(app)
    
    # Configurar rate limiting
    limiter = Limiter(
        key_func=lambda: get_client_ip(request),
        default_limits=["1000 per day", "100 per hour"]
    )
    limiter.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    
    # Importar e registrar rotas públicas
    from src.routes.public import public_bp
    app.register_blueprint(public_bp, url_prefix='/api/public')
    
    # Importar e registrar rotas de pagamento
    from src.routes.payments import payments_bp
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    
    # Importar e registrar rotas administrativas
    from src.routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Handlers de erro JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token expirado'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Token inválido'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Token de autorização necessário'}), 401
    
    # Handler de erro para rate limiting
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'error': 'Muitas tentativas. Tente novamente mais tarde.',
            'retry_after': e.retry_after
        }), 429
    
    # Handler de erro genérico
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Erro interno: {error}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint não encontrado'}), 404
    
    # Middleware para logging de requisições
    @app.before_request
    def log_request_info():
        if not request.path.startswith('/api'):
            return
        
        app.logger.info(f"{request.method} {request.path} - IP: {get_client_ip(request)}")
    
    # Rota de health check
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    # Rota para servir arquivos estáticos do frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return jsonify({'error': 'Frontend não configurado'}), 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({'error': 'Frontend não encontrado'}), 404
    
    # Criar tabelas do banco de dados
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Tabelas do banco de dados criadas/verificadas")
        except Exception as e:
            app.logger.error(f"Erro ao criar tabelas: {e}")
    
    return app

# Criar aplicação
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
