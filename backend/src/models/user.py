import uuid
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    pass_hash = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    profile_image_url = db.Column(db.Text)
    plan_type = db.Column(db.Enum('free', 'monthly24_99', 'premium', name='plan_types'), default='free')
    plan_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    ban_reason = db.Column(db.Text)
    reveal_balance = db.Column(db.Integer, default=0, nullable=False)
    system_messages_enabled = db.Column(db.Boolean, default=False, nullable=False)
    system_messages_frequency = db.Column(db.Integer, default=0, nullable=False)
    
    # Relacionamentos
    messages = db.relationship('Message', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    reveal_logs = db.relationship('RevealLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.slug and self.display_name:
            self.slug = self.generate_unique_slug(self.display_name)
    
    def set_password(self, password):
        """Define a senha do usuário com hash seguro"""
        self.pass_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.pass_hash, password)
    
    @staticmethod
    def validate_password(password):
        """Valida se a senha atende aos critérios de segurança"""
        if len(password) < 10:
            return False, "Senha deve ter pelo menos 10 caracteres"
        
        if not re.search(r'[A-Z]', password):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        
        if not re.search(r'[a-z]', password):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        
        if not re.search(r'[0-9]', password):
            return False, "Senha deve conter pelo menos um número"
        
        if not re.search(r'[^A-Za-z0-9]', password):
            return False, "Senha deve conter pelo menos um símbolo"
        
        return True, "Senha válida"
    
    @staticmethod
    def validate_age(dob):
        """Valida se o usuário tem pelo menos 16 anos"""
        if not dob:
            return False, "Data de nascimento é obrigatória"
        
        today = datetime.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if age < 16:
            return False, "Você deve ter pelo menos 16 anos"
        
        return True, "Idade válida"
    
    def generate_unique_slug(self, base_name):
        """Gera um slug único baseado no nome"""
        # Limpar e formatar o nome base
        base_slug = re.sub(r'[^a-zA-Z0-9]', '', base_name.lower())
        
        if not base_slug:
            base_slug = 'user'
        
        # Tentar o slug base primeiro
        slug = base_slug
        counter = 0
        
        # Se já existe, adicionar números até encontrar um único
        while User.query.filter_by(slug=slug).first():
            counter += 1
            slug = f"{base_slug}{counter}"
        
        return slug
    
    def is_premium(self):
        """Verifica se o usuário tem plano premium ativo"""
        if self.plan_type == 'free':
            return False
        
        if self.plan_expires_at and self.plan_expires_at < datetime.utcnow():
            # Plano expirado, reverter para free
            self.plan_type = 'free'
            self.plan_expires_at = None
            db.session.commit()
            return False
        
        return True
    
    def can_reveal(self):
        """Verifica se o usuário pode fazer revelações"""
        return self.is_premium() or self.reveal_balance > 0
    
    def use_reveal(self):
        """Usa uma revelação do saldo do usuário"""
        if self.is_premium():
            return True
        
        if self.reveal_balance > 0:
            self.reveal_balance -= 1
            return True
        
        return False
    
    def add_reveal_balance(self, amount):
        """Adiciona revelações ao saldo do usuário"""
        self.reveal_balance += amount
    
    def extend_premium(self, months=1):
        """Estende o plano premium por X meses"""
        if self.plan_expires_at and self.plan_expires_at > datetime.utcnow():
            # Estender a partir da data atual de expiração
            self.plan_expires_at += timedelta(days=30 * months)
        else:
            # Novo plano premium
            self.plan_expires_at = datetime.utcnow() + timedelta(days=30 * months)
        
        self.plan_type = 'monthly24_99'
    
    def get_public_profile(self):
        """Retorna dados públicos do perfil"""
        return {
            'slug': self.slug,
            'display_name': self.display_name,
            'profile_image_url': self.profile_image_url,
            'created_at': self.created_at.isoformat(),
            'message_count': self.messages.count()
        }
    
    def to_dict(self, include_sensitive=False):
        """Converte o usuário para dicionário"""
        data = {
            'id': self.id,
            'email': self.email,
            'email_verified': self.email_verified,
            'slug': self.slug,
            'display_name': self.display_name,
            'dob': self.dob.isoformat() if self.dob else None,
            'profile_image_url': self.profile_image_url,
            'plan_type': self.plan_type,
            'plan_expires_at': self.plan_expires_at.isoformat() if self.plan_expires_at else None,
            'created_at': self.created_at.isoformat(),
            'is_banned': self.is_banned,
            'reveal_balance': self.reveal_balance,
            'system_messages_enabled': self.system_messages_enabled,
            'system_messages_frequency': self.system_messages_frequency,
            'is_premium': self.is_premium()
        }
        
        if include_sensitive:
            data.update({
                'ban_reason': self.ban_reason
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.slug}>'
