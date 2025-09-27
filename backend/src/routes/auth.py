import uuid
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Message as MailMessage
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash

from src.models import db
from src.models.user import User
from src.models.admin import AdminAuditLog
from src.utils.email import send_email
from src.utils.security import hash_ip, generate_secure_token
from src.utils.validation import validate_request_data

auth_bp = Blueprint('auth', __name__)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("5 per minute")
def signup():
    """Registro de novo usuário"""
    try:
        # Validar dados de entrada
        required_fields = ['email', 'password', 'confirmPassword', 'displayName', 'dob']
        data = validate_request_data(request.json, required_fields)
        
        # Validar email
        try:
            valid_email = validate_email(data['email'])
            email = valid_email.email
        except EmailNotValidError:
            return jsonify({'error': 'Email inválido'}), 400
        
        # Verificar se email já existe
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já está em uso'}), 400
        
        # Validar senha
        is_valid, message = User.validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Verificar se senhas coincidem
        if data['password'] != data['confirmPassword']:
            return jsonify({'error': 'Senhas não coincidem'}), 400
        
        # Validar data de nascimento
        try:
            dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Data de nascimento inválida'}), 400
        
        is_valid_age, age_message = User.validate_age(dob)
        if not is_valid_age:
            return jsonify({'error': age_message}), 400
        
        # Criar usuário
        user = User(
            email=email,
            display_name=data['displayName'],
            dob=dob
        )
        user.set_password(data['password'])
        
        # Gerar slug único
        user.slug = user.generate_unique_slug(data['displayName'])
        
        db.session.add(user)
        db.session.commit()
        
        # Enviar email de verificação
        verification_token = generate_secure_token()
        # TODO: Armazenar token de verificação (implementar tabela de tokens)
        
        verification_url = f"{current_app.config['APP_URL']}/verify-email?token={verification_token}"
        
        try:
            send_email(
                to=email,
                subject='Verifique sua conta ANONYMOUS',
                template='verify_email',
                user=user,
                verification_url=verification_url
            )
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar email de verificação: {e}")
            # Não falhar o registro por causa do email
        
        return jsonify({
            'message': 'Conta criada com sucesso! Verifique seu email para ativar sua conta.',
            'user_id': user.id,
            'slug': user.slug
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no signup: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login do usuário"""
    try:
        # Validar dados de entrada
        required_fields = ['email', 'password']
        data = validate_request_data(request.json, required_fields)
        
        # Buscar usuário
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Email ou senha incorretos'}), 401
        
        # Verificar se usuário está banido
        if user.is_banned:
            return jsonify({'error': 'Conta suspensa. Entre em contato com o suporte.'}), 403
        
        # Verificar se email foi verificado
        if not user.email_verified:
            return jsonify({'error': 'Email não verificado. Verifique sua caixa de entrada.'}), 403
        
        # Criar token JWT
        access_token = create_access_token(
            identity=user.id,
            expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        )
        
        # Log da ação
        AdminAuditLog.log_action(
            admin_id=user.id,
            action='user_login',
            details={
                'ip': hash_ip(request.remote_addr),
                'user_agent': request.headers.get('User-Agent', '')
            }
        )
        
        return jsonify({
            'token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro no login: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per minute")
def forgot_password():
    """Solicitar recuperação de senha"""
    try:
        # Validar dados de entrada
        required_fields = ['email']
        data = validate_request_data(request.json, required_fields)
        
        # Buscar usuário
        user = User.query.filter_by(email=data['email']).first()
        
        # Sempre retornar sucesso por segurança (não revelar se email existe)
        if user and not user.is_banned:
            # Gerar token de recuperação
            reset_token = generate_secure_token()
            # TODO: Armazenar token de recuperação (implementar tabela de tokens)
            
            reset_url = f"{current_app.config['APP_URL']}/reset-password?token={reset_token}"
            
            try:
                send_email(
                    to=user.email,
                    subject='Recuperação de senha ANONYMOUS',
                    template='reset_password',
                    user=user,
                    reset_url=reset_url
                )
            except Exception as e:
                current_app.logger.error(f"Erro ao enviar email de recuperação: {e}")
        
        return jsonify({
            'message': 'Se o email existir em nossa base, você receberá um link de recuperação.'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro no forgot password: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per minute")
def reset_password():
    """Redefinir senha com token"""
    try:
        # Validar dados de entrada
        required_fields = ['token', 'password']
        data = validate_request_data(request.json, required_fields)
        
        # TODO: Validar token de recuperação (implementar verificação de token)
        # Por enquanto, simular validação
        token = data['token']
        if not token or len(token) < 32:
            return jsonify({'error': 'Token inválido ou expirado'}), 400
        
        # Validar nova senha
        is_valid, message = User.validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # TODO: Buscar usuário pelo token
        # Por enquanto, retornar erro genérico
        return jsonify({'error': 'Token inválido ou expirado'}), 400
        
    except Exception as e:
        current_app.logger.error(f"Erro no reset password: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/verify-email', methods=['POST'])
@limiter.limit("10 per minute")
def verify_email():
    """Verificar email com token"""
    try:
        # Validar dados de entrada
        required_fields = ['token']
        data = validate_request_data(request.json, required_fields)
        
        # TODO: Validar token de verificação (implementar verificação de token)
        # Por enquanto, simular validação
        token = data['token']
        if not token or len(token) < 32:
            return jsonify({'error': 'Token inválido ou expirado'}), 400
        
        # TODO: Buscar usuário pelo token e marcar como verificado
        # Por enquanto, retornar erro genérico
        return jsonify({'error': 'Token inválido ou expirado'}), 400
        
    except Exception as e:
        current_app.logger.error(f"Erro na verificação de email: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obter dados do usuário atual"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if user.is_banned:
            return jsonify({'error': 'Conta suspensa'}), 403
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter usuário atual: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Renovar token de acesso"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário inválido'}), 401
        
        # Criar novo token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        )
        
        return jsonify({
            'token': access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao renovar token: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
