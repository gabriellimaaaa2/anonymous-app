import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src.models import db
from src.models.user import User
from src.models.message import Message, BannedIP
from src.models.payment import IPVault
from src.utils.security import hash_ip, encrypt_ip, get_client_ip
from src.utils.geoip import get_location_for_ip, calculate_location_confidence
from src.utils.moderation import moderate_content
from src.utils.validation import validate_request_data, validate_message_text

public_bp = Blueprint('public', __name__)

# Rate limiting específico para rotas públicas
limiter = Limiter(
    key_func=lambda: get_client_ip(request),
    default_limits=["100 per hour", "10 per minute"]
)

@public_bp.route('/<slug>', methods=['GET'])
def get_user_profile(slug):
    """Obtém perfil público do usuário pelo slug"""
    try:
        user = User.query.filter_by(slug=slug).first()
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if user.is_banned:
            return jsonify({'error': 'Perfil não disponível'}), 403
        
        # Contar mensagens recebidas (apenas aprovadas)
        message_count = Message.query.filter_by(
            slug_owner=slug,
            moderation_status='approved'
        ).count()
        
        return jsonify({
            'user': {
                'slug': user.slug,
                'display_name': user.display_name,
                'bio': user.bio,
                'avatar_url': user.avatar_url,
                'created_at': user.created_at.isoformat(),
                'message_count': message_count,
                'is_verified': user.email_verified
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter perfil {slug}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/<slug>/send', methods=['POST'])
@limiter.limit("5 per minute")
def send_anonymous_message(slug):
    """Envia mensagem anônima para um usuário"""
    try:
        # Validar dados de entrada
        required_fields = ['text']
        optional_fields = ['audio_url']
        data = validate_request_data(request.json, required_fields, optional_fields)
        
        # Verificar se usuário existe
        user = User.query.filter_by(slug=slug).first()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if user.is_banned:
            return jsonify({'error': 'Usuário não está aceitando mensagens'}), 403
        
        # Validar texto da mensagem
        is_valid, message = validate_message_text(data['text'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Obter IP do cliente
        client_ip = get_client_ip(request)
        ip_hash = hash_ip(client_ip)
        
        # Verificar se IP está banido
        banned_ip = BannedIP.query.filter_by(ip_hash=ip_hash).first()
        if banned_ip:
            return jsonify({'error': 'Você foi bloqueado de enviar mensagens'}), 403
        
        # Verificar rate limit por IP (máximo 10 mensagens por hora)
        recent_messages = Message.query.filter(
            Message.ip_hash == ip_hash,
            Message.created_at >= datetime.utcnow().replace(hour=datetime.utcnow().hour, minute=0, second=0, microsecond=0)
        ).count()
        
        if recent_messages >= 10:
            return jsonify({'error': 'Limite de mensagens por hora excedido'}), 429
        
        # Obter informações de localização
        location_info = get_location_for_ip(client_ip)
        
        # Moderar conteúdo
        moderation_result = moderate_content(data['text'])
        
        # Determinar status inicial baseado na moderação
        if moderation_result['action'] == 'block':
            return jsonify({'error': 'Mensagem bloqueada por violar nossas diretrizes'}), 400
        elif moderation_result['action'] == 'flag':
            initial_status = 'pending'
        else:
            initial_status = 'approved'
        
        # Criar mensagem
        message = Message(
            slug_owner=slug,
            text=data['text'],
            audio_url=data.get('audio_url'),
            ip_hash=ip_hash,
            geo_country=location_info.get('country'),
            geo_region=location_info.get('region'),
            geo_city=location_info.get('city'),
            geo_lat=location_info.get('lat'),
            geo_lon=location_info.get('lon'),
            provider_confidence=location_info.get('confidence', 0),
            vpn_flag=location_info.get('vpn_flag', False),
            ua=request.headers.get('User-Agent', ''),
            accept_language=request.headers.get('Accept-Language', ''),
            moderation_status=initial_status
        )
        
        # Calcular score de confiança
        message.calculate_confidence_score()
        
        db.session.add(message)
        db.session.flush()  # Para obter o ID da mensagem
        
        # Armazenar IP encriptado no vault
        encrypted_ip, salt = encrypt_ip(client_ip)
        ip_vault = IPVault(
            message_id=message.id,
            ip_encrypted=encrypted_ip,
            salt=salt
        )
        db.session.add(ip_vault)
        
        db.session.commit()
        
        # Log da ação
        current_app.logger.info(f"Mensagem enviada para {slug} - ID: {message.id[:8]}... Status: {initial_status}")
        
        # Se foi flagada, adicionar à fila de moderação
        if initial_status == 'pending':
            from src.models.admin import ModerationQueue
            mod_queue = ModerationQueue(
                message_id=message.id,
                priority='medium' if moderation_result.get('severity') == 'medium' else 'low',
                reason=', '.join(moderation_result.get('reasons', [])),
                auto_flagged=True
            )
            db.session.add(mod_queue)
            db.session.commit()
        
        return jsonify({
            'message': 'Mensagem enviada com sucesso!',
            'message_id': message.id,
            'status': initial_status,
            'location': {
                'city': message.geo_city,
                'region': message.geo_region,
                'country': message.geo_country,
                'confidence': message.get_confidence_label()
            } if message.geo_city else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao enviar mensagem para {slug}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/<slug>/stats', methods=['GET'])
def get_user_stats(slug):
    """Obtém estatísticas públicas do usuário"""
    try:
        user = User.query.filter_by(slug=slug).first()
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if user.is_banned:
            return jsonify({'error': 'Perfil não disponível'}), 403
        
        # Contar mensagens por status
        total_messages = Message.query.filter_by(slug_owner=slug).count()
        approved_messages = Message.query.filter_by(
            slug_owner=slug,
            moderation_status='approved'
        ).count()
        
        # Estatísticas de localização (apenas mensagens aprovadas)
        location_stats = db.session.query(
            Message.geo_country,
            Message.geo_region,
            db.func.count(Message.id).label('count')
        ).filter(
            Message.slug_owner == slug,
            Message.moderation_status == 'approved',
            Message.geo_country.isnot(None)
        ).group_by(
            Message.geo_country,
            Message.geo_region
        ).order_by(
            db.func.count(Message.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'stats': {
                'total_messages': total_messages,
                'approved_messages': approved_messages,
                'top_locations': [
                    {
                        'country': stat.geo_country,
                        'region': stat.geo_region,
                        'count': stat.count
                    }
                    for stat in location_stats
                ]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter stats de {slug}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/check-slug/<slug>', methods=['GET'])
def check_slug_availability(slug):
    """Verifica se um slug está disponível"""
    try:
        # Validar formato do slug
        from src.utils.validation import validate_slug
        is_valid, message = validate_slug(slug)
        
        if not is_valid:
            return jsonify({
                'available': False,
                'reason': message
            }), 200
        
        # Verificar se já existe
        existing_user = User.query.filter_by(slug=slug).first()
        
        return jsonify({
            'available': existing_user is None,
            'reason': 'Slug já está em uso' if existing_user else None
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar slug {slug}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/report-message', methods=['POST'])
@limiter.limit("3 per minute")
def report_message():
    """Reporta uma mensagem por conteúdo inadequado"""
    try:
        # Validar dados de entrada
        required_fields = ['message_id', 'reason']
        data = validate_request_data(request.json, required_fields)
        
        # Verificar se mensagem existe
        message = Message.query.get(data['message_id'])
        if not message:
            return jsonify({'error': 'Mensagem não encontrada'}), 404
        
        # Incrementar contador de reports
        message.reports_count += 1
        
        # Se atingir 3 reports, flaggar automaticamente
        if message.reports_count >= 3 and message.moderation_status == 'approved':
            message.moderation_status = 'flagged'
            
            # Adicionar à fila de moderação
            from src.models.admin import ModerationQueue
            existing_queue = ModerationQueue.query.filter_by(message_id=message.id).first()
            if not existing_queue:
                mod_queue = ModerationQueue(
                    message_id=message.id,
                    priority='high',
                    reason=f"Múltiplos reports: {data['reason']}",
                    flagged_by_reports=True
                )
                db.session.add(mod_queue)
        
        db.session.commit()
        
        current_app.logger.info(f"Mensagem {message.id[:8]}... reportada. Total reports: {message.reports_count}")
        
        return jsonify({
            'message': 'Report enviado com sucesso. Obrigado por ajudar a manter nossa comunidade segura.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao reportar mensagem: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
