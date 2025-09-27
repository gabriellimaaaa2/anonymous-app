import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

class AdminAuditLog(db.Model):
    __tablename__ = 'admin_audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = db.Column(db.String(36), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(100))
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relacionamento será adicionado depois que a tabela users for criada
    
    @staticmethod
    def log_action(admin_id, action, target=None, details=None):
        """Registra uma ação do admin"""
        log = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target=target,
            details=details
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_email': None,  # TODO: Implementar lookup do admin
            'action': self.action,
            'target': self.target,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<AdminAuditLog {self.action} by {self.admin_id[:8]}...>'


class AdminSession(db.Model):
    """Sessões de admin com MFA"""
    __tablename__ = 'admin_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    mfa_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relacionamento será adicionado depois
    
    def is_expired(self):
        """Verifica se a sessão expirou"""
        return datetime.utcnow() > self.expires_at
    
    def update_activity(self):
        """Atualiza a última atividade"""
        self.last_activity = datetime.utcnow()
    
    def revoke(self):
        """Revoga a sessão"""
        self.is_active = False
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mfa_verified': self.mfa_verified,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active,
            'is_expired': self.is_expired()
        }
    
    def __repr__(self):
        return f'<AdminSession {self.id[:8]}... for {self.user_id[:8]}...>'


class ModerationQueue(db.Model):
    """Fila de moderação para mensagens flagadas"""
    __tablename__ = 'moderation_queue'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = db.Column(db.String(36), nullable=False, unique=True)
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='moderation_priorities'), default='medium')
    reason = db.Column(db.String(100))
    auto_flagged = db.Column(db.Boolean, default=False, nullable=False)
    flagged_by_reports = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.String(36))
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'escalated', name='moderation_statuses'), default='pending')
    moderator_notes = db.Column(db.Text)
    
    # Relacionamentos serão adicionados depois
    
    def mark_reviewed(self, admin_id, status, notes=None):
        """Marca como revisado"""
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = admin_id
        self.status = status
        self.moderator_notes = notes
    
    def escalate(self, reason=None):
        """Escalona para revisão superior"""
        self.status = 'escalated'
        self.priority = 'urgent'
        if reason:
            self.moderator_notes = f"Escalated: {reason}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'priority': self.priority,
            'reason': self.reason,
            'auto_flagged': self.auto_flagged,
            'flagged_by_reports': self.flagged_by_reports,
            'created_at': self.created_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
            'status': self.status,
            'moderator_notes': self.moderator_notes,
            'message': None  # TODO: Implementar lookup da mensagem
        }
    
    def __repr__(self):
        return f'<ModerationQueue {self.id[:8]}... {self.priority} {self.status}>'



class AdminUser(db.Model):
    """Usuários administrativos com diferentes níveis de acesso"""
    __tablename__ = 'admin_users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, unique=True)
    role = db.Column(db.Enum('viewer', 'moderator', 'admin', 'super_admin', name='admin_roles'), default='viewer')
    permissions = db.Column(db.JSON)  # Permissões específicas
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(36))
    last_login = db.Column(db.DateTime)
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    mfa_secret = db.Column(db.String(32))  # TOTP secret
    
    def has_permission(self, permission):
        """Verifica se tem uma permissão específica"""
        if not self.is_active:
            return False
        
        # Super admin tem todas as permissões
        if self.role == 'super_admin':
            return True
        
        # Verificar permissões específicas
        if self.permissions and permission in self.permissions:
            return self.permissions[permission]
        
        # Permissões padrão por role
        default_permissions = {
            'viewer': ['view_dashboard', 'view_users', 'view_messages'],
            'moderator': ['view_dashboard', 'view_users', 'view_messages', 'moderate_messages', 'ban_users'],
            'admin': ['view_dashboard', 'view_users', 'view_messages', 'moderate_messages', 'ban_users', 'view_analytics', 'manage_config'],
            'super_admin': ['*']  # Todas as permissões
        }
        
        role_permissions = default_permissions.get(self.role, [])
        return permission in role_permissions or '*' in role_permissions
    
    def update_last_login(self):
        """Atualiza último login"""
        self.last_login = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'mfa_enabled': self.mfa_enabled
        }
    
    def __repr__(self):
        return f'<AdminUser {self.user_id[:8]}... {self.role}>'


class SystemConfig(db.Model):
    """Configurações do sistema"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')
    is_public = db.Column(db.Boolean, default=False, nullable=False)  # Se pode ser acessado publicamente
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(36))
    
    @staticmethod
    def get_value(key, default=None):
        """Obtém valor de configuração"""
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default
    
    @staticmethod
    def set_value(key, value, description=None, category='general', updated_by=None):
        """Define valor de configuração"""
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = str(value)
            config.updated_at = datetime.utcnow()
            config.updated_by = updated_by
        else:
            config = SystemConfig(
                key=key,
                value=str(value),
                description=description,
                category=category,
                updated_by=updated_by
            )
            db.session.add(config)
        
        db.session.commit()
        return config
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'updated_by': self.updated_by
        }
    
    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value[:20]}...>'
