import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import func, desc, asc

from src.models import db
from src.models.user import User
from src.models.message import Message, BannedIP
from src.models.payment import Payment, RevealLog
from src.models.admin import AdminUser, AdminAuditLog, ModerationQueue, SystemConfig
from src.utils.security import get_client_ip
from src.utils.validation import validate_request_data, validate_pagination

admin_bp = Blueprint('admin', __name__)

# Rate limiting para rotas administrativas
limiter = Limiter(
    key_func=lambda: get_client_ip(request),
    default_limits=["1000 per hour", "100 per minute"]
)

def require_admin_role(required_role='admin'):
    """Decorator para verificar se o usuário é admin"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            admin_user = AdminUser.query.filter_by(user_id=user_id).first()
            
            if not admin_user or not admin_user.is_active:
                return jsonify({'error': 'Acesso negado - Admin necessário'}), 403
            
            role_hierarchy = {'viewer': 1, 'moderator': 2, 'admin': 3, 'super_admin': 4}
            user_level = role_hierarchy.get(admin_user.role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            
            if user_level < required_level:
                return jsonify({'error': f'Acesso negado - Role {required_role} necessário'}), 403
            
            # Log da ação
            log_admin_action(admin_user.id, f.__name__, request.method, request.path)
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def log_admin_action(admin_id, action, method, path, details=None):
    """Log de ações administrativas"""
    try:
        audit_log = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            details=details or f"{method} {path}",
            ip_address=get_client_ip(request)
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Erro ao criar log de auditoria: {e}")

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_admin_role('viewer')
def get_admin_dashboard():
    """Dashboard administrativo com métricas gerais"""
    try:
        # Métricas gerais
        total_users = User.query.count()
        active_users = User.query.filter_by(is_banned=False).count()
        total_messages = Message.query.count()
        pending_messages = Message.query.filter_by(moderation_status='pending').count()
        
        # Métricas de receita
        total_revenue = db.session.query(func.sum(Payment.amount_brl)).filter_by(status='completed').scalar() or 0
        monthly_revenue = db.session.query(func.sum(Payment.amount_brl)).filter(
            Payment.status == 'completed',
            Payment.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ).scalar() or 0
        
        # Usuários por dia (últimos 30 dias)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_users = db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= thirty_days_ago
        ).group_by(
            func.date(User.created_at)
        ).order_by('date').all()
        
        # Mensagens por dia (últimos 30 dias)
        daily_messages = db.session.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('count')
        ).filter(
            Message.created_at >= thirty_days_ago
        ).group_by(
            func.date(Message.created_at)
        ).order_by('date').all()
        
        # Top países por mensagens
        top_countries = db.session.query(
            Message.geo_country,
            func.count(Message.id).label('count')
        ).filter(
            Message.geo_country.isnot(None)
        ).group_by(
            Message.geo_country
        ).order_by(
            desc('count')
        ).limit(10).all()
        
        # Fila de moderação
        moderation_queue_count = ModerationQueue.query.filter_by(status='pending').count()
        
        return jsonify({
            'dashboard': {
                'metrics': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'total_messages': total_messages,
                    'pending_messages': pending_messages,
                    'total_revenue': float(total_revenue),
                    'monthly_revenue': float(monthly_revenue),
                    'moderation_queue': moderation_queue_count
                },
                'charts': {
                    'daily_users': [
                        {'date': item.date.isoformat(), 'count': item.count}
                        for item in daily_users
                    ],
                    'daily_messages': [
                        {'date': item.date.isoformat(), 'count': item.count}
                        for item in daily_messages
                    ],
                    'top_countries': [
                        {'country': item.geo_country, 'count': item.count}
                        for item in top_countries
                    ]
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard admin: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin_role('moderator')
def get_users():
    """Lista usuários com filtros e paginação"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', 'all')  # all, active, banned
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validar paginação
        is_valid, message, page, per_page = validate_pagination(page, per_page, 100)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Construir query
        query = User.query
        
        # Filtros
        if search:
            query = query.filter(
                db.or_(
                    User.email.ilike(f'%{search}%'),
                    User.display_name.ilike(f'%{search}%'),
                    User.slug.ilike(f'%{search}%')
                )
            )
        
        if status == 'active':
            query = query.filter_by(is_banned=False)
        elif status == 'banned':
            query = query.filter_by(is_banned=True)
        
        # Ordenação
        if hasattr(User, sort_by):
            if sort_order == 'desc':
                query = query.order_by(desc(getattr(User, sort_by)))
            else:
                query = query.order_by(asc(getattr(User, sort_by)))
        
        # Paginação
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = []
        for user in pagination.items:
            user_data = user.to_dict(include_private=True)
            
            # Adicionar estatísticas
            user_data['stats'] = {
                'total_messages': Message.query.filter_by(slug_owner=user.slug).count(),
                'total_payments': Payment.query.filter_by(user_id=user.id).count(),
                'total_reveals': RevealLog.query.filter_by(user_id=user.id).count()
            }
            
            users.append(user_data)
        
        return jsonify({
            'users': users,
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
        current_app.logger.error(f"Erro ao listar usuários: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/users/<user_id>/ban', methods=['POST'])
@jwt_required()
@require_admin_role('moderator')
def ban_user(user_id):
    """Banir ou desbanir usuário"""
    try:
        admin_id = get_jwt_identity()
        
        # Validar dados
        data = validate_request_data(request.json, [], ['reason', 'permanent'])
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Alternar status de ban
        user.is_banned = not user.is_banned
        user.ban_reason = data.get('reason') if user.is_banned else None
        user.banned_at = datetime.utcnow() if user.is_banned else None
        user.updated_at = datetime.utcnow()
        
        action = 'ban' if user.is_banned else 'unban'
        
        # Log da ação
        log_admin_action(
            admin_id, 
            f'{action}_user',
            'POST',
            f'/admin/users/{user_id}/ban',
            f"Usuário {user.email} {'banido' if user.is_banned else 'desbanido'}. Motivo: {data.get('reason', 'N/A')}"
        )
        
        db.session.commit()
        
        return jsonify({
            'message': f'Usuário {"banido" if user.is_banned else "desbanido"} com sucesso',
            'user': user.to_dict(include_private=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao banir usuário: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/moderation/queue', methods=['GET'])
@jwt_required()
@require_admin_role('moderator')
def get_moderation_queue():
    """Fila de moderação de mensagens"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        priority = request.args.get('priority', 'all')  # all, high, medium, low
        
        # Validar paginação
        is_valid, message, page, per_page = validate_pagination(page, per_page, 50)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Construir query
        query = ModerationQueue.query.filter_by(status='pending')
        
        if priority != 'all':
            query = query.filter_by(priority=priority)
        
        # Ordenar por prioridade e data
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        query = query.order_by(
            desc(func.case(
                (ModerationQueue.priority == 'high', 3),
                (ModerationQueue.priority == 'medium', 2),
                else_=1
            )),
            asc(ModerationQueue.created_at)
        )
        
        # Paginação
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        queue_items = []
        for item in pagination.items:
            item_data = item.to_dict()
            
            # Adicionar dados da mensagem
            message = Message.query.get(item.message_id)
            if message:
                item_data['message'] = message.to_dict(include_location=True, include_sensitive=True)
            
            queue_items.append(item_data)
        
        return jsonify({
            'queue': queue_items,
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
        current_app.logger.error(f"Erro na fila de moderação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/moderation/queue/<queue_id>/moderate', methods=['POST'])
@jwt_required()
@require_admin_role('moderator')
def moderate_message(queue_id):
    """Moderar uma mensagem da fila"""
    try:
        admin_id = get_jwt_identity()
        
        # Validar dados
        required_fields = ['action']  # approve, reject, flag
        optional_fields = ['reason', 'notes']
        data = validate_request_data(request.json, required_fields, optional_fields)
        
        if data['action'] not in ['approve', 'reject', 'flag']:
            return jsonify({'error': 'Ação inválida'}), 400
        
        # Buscar item da fila
        queue_item = ModerationQueue.query.get(queue_id)
        if not queue_item:
            return jsonify({'error': 'Item não encontrado'}), 404
        
        # Buscar mensagem
        message = Message.query.get(queue_item.message_id)
        if not message:
            return jsonify({'error': 'Mensagem não encontrada'}), 404
        
        # Aplicar moderação
        if data['action'] == 'approve':
            message.moderation_status = 'approved'
        elif data['action'] == 'reject':
            message.moderation_status = 'blocked'
        elif data['action'] == 'flag':
            message.moderation_status = 'flagged'
        
        # Atualizar item da fila
        queue_item.status = 'completed'
        queue_item.moderated_by = admin_id
        queue_item.moderated_at = datetime.utcnow()
        queue_item.moderator_notes = data.get('notes')
        
        # Log da ação
        log_admin_action(
            admin_id,
            'moderate_message',
            'POST',
            f'/admin/moderation/queue/{queue_id}/moderate',
            f"Mensagem {message.id[:8]}... {data['action']}. Motivo: {data.get('reason', 'N/A')}"
        )
        
        db.session.commit()
        
        return jsonify({
            'message': f'Mensagem {data["action"]} com sucesso',
            'queue_item': queue_item.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao moderar mensagem: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/analytics/revenue', methods=['GET'])
@jwt_required()
@require_admin_role('admin')
def get_revenue_analytics():
    """Análise de receita"""
    try:
        period = request.args.get('period', '30d')  # 7d, 30d, 90d, 1y
        
        # Definir período
        if period == '7d':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == '30d':
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == '90d':
            start_date = datetime.utcnow() - timedelta(days=90)
        elif period == '1y':
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            return jsonify({'error': 'Período inválido'}), 400
        
        # Receita por dia
        daily_revenue = db.session.query(
            func.date(Payment.created_at).label('date'),
            func.sum(Payment.amount_brl).label('revenue'),
            func.count(Payment.id).label('transactions')
        ).filter(
            Payment.status == 'completed',
            Payment.created_at >= start_date
        ).group_by(
            func.date(Payment.created_at)
        ).order_by('date').all()
        
        # Receita por método de pagamento
        payment_methods = db.session.query(
            Payment.payment_method,
            func.sum(Payment.amount_brl).label('revenue'),
            func.count(Payment.id).label('transactions')
        ).filter(
            Payment.status == 'completed',
            Payment.created_at >= start_date
        ).group_by(
            Payment.payment_method
        ).all()
        
        # Receita por pacote
        package_revenue = db.session.query(
            Payment.package_id,
            func.sum(Payment.amount_brl).label('revenue'),
            func.count(Payment.id).label('transactions')
        ).filter(
            Payment.status == 'completed',
            Payment.created_at >= start_date
        ).group_by(
            Payment.package_id
        ).order_by(desc('revenue')).all()
        
        # Métricas totais
        total_revenue = sum(item.revenue for item in daily_revenue)
        total_transactions = sum(item.transactions for item in daily_revenue)
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
        
        return jsonify({
            'analytics': {
                'period': period,
                'metrics': {
                    'total_revenue': float(total_revenue),
                    'total_transactions': total_transactions,
                    'avg_transaction_value': float(avg_transaction)
                },
                'charts': {
                    'daily_revenue': [
                        {
                            'date': item.date.isoformat(),
                            'revenue': float(item.revenue),
                            'transactions': item.transactions
                        }
                        for item in daily_revenue
                    ],
                    'payment_methods': [
                        {
                            'method': item.payment_method,
                            'revenue': float(item.revenue),
                            'transactions': item.transactions
                        }
                        for item in payment_methods
                    ],
                    'package_revenue': [
                        {
                            'package': item.package_id,
                            'revenue': float(item.revenue),
                            'transactions': item.transactions
                        }
                        for item in package_revenue
                    ]
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro na análise de receita: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/system/config', methods=['GET'])
@jwt_required()
@require_admin_role('admin')
def get_system_config():
    """Configurações do sistema"""
    try:
        configs = SystemConfig.query.all()
        config_dict = {config.key: config.value for config in configs}
        
        return jsonify({'config': config_dict}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter configurações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/system/config', methods=['PUT'])
@jwt_required()
@require_admin_role('super_admin')
def update_system_config():
    """Atualizar configurações do sistema"""
    try:
        admin_id = get_jwt_identity()
        data = request.json
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        updated_configs = []
        
        for key, value in data.items():
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    key=key,
                    value=str(value),
                    description=f'Configuração {key}'
                )
                db.session.add(config)
            
            updated_configs.append(key)
        
        # Log da ação
        log_admin_action(
            admin_id,
            'update_system_config',
            'PUT',
            '/admin/system/config',
            f"Configurações atualizadas: {', '.join(updated_configs)}"
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Configurações atualizadas com sucesso',
            'updated_configs': updated_configs
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar configurações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_bp.route('/audit-log', methods=['GET'])
@jwt_required()
@require_admin_role('admin')
def get_audit_log():
    """Log de auditoria administrativa"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        admin_id = request.args.get('admin_id')
        action = request.args.get('action')
        
        # Validar paginação
        is_valid, message, page, per_page = validate_pagination(page, per_page, 100)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Construir query
        query = AdminAuditLog.query
        
        if admin_id:
            query = query.filter_by(admin_id=admin_id)
        
        if action:
            query = query.filter(AdminAuditLog.action.ilike(f'%{action}%'))
        
        # Ordenar por data (mais recente primeiro)
        query = query.order_by(desc(AdminAuditLog.created_at))
        
        # Paginação
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'audit_log': [log.to_dict() for log in pagination.items],
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
        current_app.logger.error(f"Erro no log de auditoria: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
