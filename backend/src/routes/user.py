import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src.models import db
from src.models.user import User
from src.models.message import Message
from src.models.payment import RevealLog
from src.utils.security import get_client_ip
from src.utils.validation import validate_request_data, validate_pagination, validate_sort_params

user_bp = Blueprint('user', __name__)

# Rate limiting para rotas de usuário
limiter = Limiter(
    key_func=lambda: get_client_ip(request),
    default_limits=["500 per hour", "50 per minute"]
)

@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Obtém dados do dashboard do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        # Estatísticas gerais
        total_messages = Message.query.filter_by(slug_owner=user.slug).count()
        approved_messages = Message.query.filter_by(
            slug_owner=user.slug,
            moderation_status='approved'
        ).count()
        pending_messages = Message.query.filter_by(
            slug_owner=user.slug,
            moderation_status='pending'
        ).count()
        
        # Mensagens recentes (últimas 7 dias)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_messages = Message.query.filter(
            Message.slug_owner == user.slug,
            Message.created_at >= week_ago,
            Message.moderation_status == 'approved'
        ).count()
        
        # Revelações feitas
        total_reveals = RevealLog.query.filter_by(user_id=user.id).count()
        
        # Top países/regiões
        location_stats = db.session.query(
            Message.geo_country,
            Message.geo_region,
            db.func.count(Message.id).label('count')
        ).filter(
            Message.slug_owner == user.slug,
            Message.moderation_status == 'approved',
            Message.geo_country.isnot(None)
        ).group_by(
            Message.geo_country,
            Message.geo_region
        ).order_by(
            db.func.count(Message.id).desc()
        ).limit(5).all()
        
        # Atividade por dia (últimos 30 dias)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_activity = db.session.query(
            db.func.date(Message.created_at).label('date'),
            db.func.count(Message.id).label('count')
        ).filter(
            Message.slug_owner == user.slug,
            Message.moderation_status == 'approved',
            Message.created_at >= thirty_days_ago
        ).group_by(
            db.func.date(Message.created_at)
        ).order_by(
            db.func.date(Message.created_at)
        ).all()
        
        return jsonify({
            'dashboard': {
                'user': user.to_dict(),
                'stats': {
                    'total_messages': total_messages,
                    'approved_messages': approved_messages,
                    'pending_messages': pending_messages,
                    'recent_messages': recent_messages,
                    'total_reveals': total_reveals,
                    'reveal_credits': user.reveal_credits
                },
                'top_locations': [
                    {
                        'country': stat.geo_country,
                        'region': stat.geo_region,
                        'count': stat.count
                    }
                    for stat in location_stats
                ],
                'daily_activity': [
                    {
                        'date': stat.date.isoformat(),
                        'count': stat.count
                    }
                    for stat in daily_activity
                ]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard do usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@user_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_user_messages():
    """Obtém mensagens do usuário com paginação e filtros"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        # Parâmetros de query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', 'approved')  # approved, pending, flagged, all
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validar paginação
        is_valid, message, page, per_page = validate_pagination(page, per_page, 50)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validar ordenação
        allowed_sort_fields = ['created_at', 'confidence_score', 'reveal_count']
        is_valid, message, sort_by, sort_order = validate_sort_params(sort_by, sort_order, allowed_sort_fields)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Construir query
        query = Message.query.filter_by(slug_owner=user.slug)
        
        # Filtrar por status
        if status != 'all':
            query = query.filter_by(moderation_status=status)
        
        # Ordenação
        if sort_order == 'desc':
            query = query.order_by(getattr(Message, sort_by).desc())
        else:
            query = query.order_by(getattr(Message, sort_by).asc())
        
        # Paginação
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        messages = []
        for message in pagination.items:
            message_data = message.to_dict(include_location=True)
            
            # Adicionar informação se foi revelada
            reveal_log = RevealLog.query.filter_by(
                message_id=message.id,
                user_id=user.id
            ).first()
            
            message_data['is_revealed'] = reveal_log is not None
            if reveal_log:
                message_data['revealed_at'] = reveal_log.created_at.isoformat()
                message_data['reveal_details'] = {
                    'city': reveal_log.city,
                    'region': reveal_log.region,
                    'confidence_score': reveal_log.confidence_score
                }
            
            messages.append(message_data)
        
        return jsonify({
            'messages': messages,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter mensagens do usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@user_bp.route('/messages/<message_id>', methods=['GET'])
@jwt_required()
def get_message_detail(message_id):
    """Obtém detalhes de uma mensagem específica"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        # Buscar mensagem
        message = Message.query.filter_by(
            id=message_id,
            slug_owner=user.slug
        ).first()
        
        if not message:
            return jsonify({'error': 'Mensagem não encontrada'}), 404
        
        # Dados da mensagem
        message_data = message.to_dict(include_location=True, include_sensitive=True)
        
        # Verificar se foi revelada
        reveal_log = RevealLog.query.filter_by(
            message_id=message.id,
            user_id=user.id
        ).first()
        
        message_data['is_revealed'] = reveal_log is not None
        if reveal_log:
            message_data['reveal_details'] = reveal_log.to_dict()
        
        # Verificar se pode ser revelada
        can_reveal, reveal_message = message.can_be_revealed(user)
        message_data['can_reveal'] = can_reveal
        message_data['reveal_message'] = reveal_message
        
        return jsonify({
            'message': message_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter detalhes da mensagem {message_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Obtém perfil completo do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        return jsonify({
            'user': user.to_dict(include_private=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter perfil do usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def update_user_profile():
    """Atualiza perfil do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        # Validar dados de entrada
        optional_fields = ['display_name', 'bio', 'avatar_url', 'instagram_username']
        data = validate_request_data(request.json, [], optional_fields)
        
        # Atualizar campos permitidos
        if 'display_name' in data:
            from src.utils.validation import validate_display_name
            is_valid, message = validate_display_name(data['display_name'])
            if not is_valid:
                return jsonify({'error': message}), 400
            user.display_name = data['display_name']
        
        if 'bio' in data:
            if len(data['bio']) > 500:
                return jsonify({'error': 'Bio muito longa (máximo 500 caracteres)'}), 400
            user.bio = data['bio']
        
        if 'avatar_url' in data:
            from src.utils.validation import validate_image_url
            is_valid, message = validate_image_url(data['avatar_url'])
            if not is_valid:
                return jsonify({'error': message}), 400
            user.avatar_url = data['avatar_url']
        
        if 'instagram_username' in data:
            instagram = data['instagram_username'].strip()
            if instagram and not instagram.startswith('@'):
                instagram = '@' + instagram
            user.instagram_username = instagram
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'user': user.to_dict(include_private=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar perfil do usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@user_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_user_settings():
    """Obtém configurações do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        return jsonify({
            'settings': {
                'email_notifications': user.email_notifications,
                'auto_approve_messages': user.auto_approve_messages,
                'allow_audio_messages': user.allow_audio_messages,
                'profile_visibility': user.profile_visibility,
                'reveal_credits': user.reveal_credits,
                'subscription_tier': user.subscription_tier
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter configurações do usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@user_bp.route('/settings', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per minute")
def update_user_settings():
    """Atualiza configurações do usuário"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        # Validar dados de entrada
        optional_fields = [
            'email_notifications', 'auto_approve_messages', 
            'allow_audio_messages', 'profile_visibility'
        ]
        data = validate_request_data(request.json, [], optional_fields)
        
        # Atualizar configurações
        if 'email_notifications' in data:
            user.email_notifications = bool(data['email_notifications'])
        
        if 'auto_approve_messages' in data:
            user.auto_approve_messages = bool(data['auto_approve_messages'])
        
        if 'allow_audio_messages' in data:
            user.allow_audio_messages = bool(data['allow_audio_messages'])
        
        if 'profile_visibility' in data:
            if data['profile_visibility'] not in ['public', 'private']:
                return jsonify({'error': 'Visibilidade deve ser public ou private'}), 400
            user.profile_visibility = data['profile_visibility']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Configurações atualizadas com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar configurações do usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
