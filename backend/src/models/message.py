import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug_owner = db.Column(db.String(50), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    audio_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_hash = db.Column(db.String(64), nullable=False)
    geo_country = db.Column(db.String(2))
    geo_region = db.Column(db.String(100))
    geo_city = db.Column(db.String(100))
    geo_lat = db.Column(db.Float)
    geo_lon = db.Column(db.Float)
    provider_confidence = db.Column(db.Integer, default=0)
    vpn_flag = db.Column(db.Boolean, default=False, nullable=False)
    ua = db.Column(db.Text)
    accept_language = db.Column(db.String(100))
    moderation_status = db.Column(db.Enum('pending', 'approved', 'blocked', 'flagged', name='moderation_statuses'), default='pending', index=True)
    reports_count = db.Column(db.Integer, default=0, nullable=False)
    is_system_message = db.Column(db.Boolean, default=False, nullable=False)
    system_template_id = db.Column(db.String(50))
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    locked_price_cents = db.Column(db.Integer, default=0)
    reveal_count = db.Column(db.Integer, default=0, nullable=False)
    last_reveal_at = db.Column(db.DateTime)
    confidence_score = db.Column(db.Integer, default=0)
    
    # Relacionamentos
    reveal_logs = db.relationship('RevealLog', backref='message', lazy='dynamic', cascade='all, delete-orphan')
    ip_vault_entry = db.relationship('IPVault', backref='message', uselist=False, cascade='all, delete-orphan')
    
    def calculate_confidence_score(self, timezone_match=False, language_match=False, history_score=0):
        """Calcula o score de confiança da localização"""
        confidence = int(self.provider_confidence * 0.5)
        
        if timezone_match:
            confidence += 15
        
        if language_match:
            confidence += 10
        
        confidence += min(15, history_score * 5)
        
        if self.vpn_flag:
            confidence -= 30
        
        # Garantir que está entre 0 e 100
        confidence = max(0, min(100, confidence))
        
        self.confidence_score = confidence
        return confidence
    
    def get_confidence_label(self):
        """Retorna o label da confiança"""
        if self.confidence_score >= 80:
            return 'ALTA'
        elif self.confidence_score >= 50:
            return 'MÉDIA'
        else:
            return 'BAIXA'
    
    def can_be_revealed(self, user):
        """Verifica se a mensagem pode ser revelada pelo usuário"""
        if not self.geo_city or not self.geo_region:
            return False, "Localização não disponível"
        
        if self.slug_owner != user.slug:
            return False, "Você não é o dono desta mensagem"
        
        if not user.can_reveal():
            return False, "Você não tem revelações disponíveis"
        
        return True, "Pode revelar"
    
    def is_flagged(self):
        """Verifica se a mensagem está sinalizada"""
        return self.moderation_status in ['flagged', 'blocked'] or self.reports_count >= 3
    
    def get_preview_text(self, max_length=150):
        """Retorna um preview do texto da mensagem"""
        if len(self.text) <= max_length:
            return self.text
        
        return self.text[:max_length] + '...'
    
    def to_dict(self, include_location=False, include_sensitive=False):
        """Converte a mensagem para dicionário"""
        data = {
            'id': self.id,
            'text': self.text,
            'audio_url': self.audio_url,
            'created_at': self.created_at.isoformat(),
            'moderation_status': self.moderation_status,
            'reports_count': self.reports_count,
            'is_system_message': self.is_system_message,
            'system_template_id': self.system_template_id,
            'is_locked': self.is_locked,
            'locked_price_cents': self.locked_price_cents,
            'reveal_count': self.reveal_count,
            'last_reveal_at': self.last_reveal_at.isoformat() if self.last_reveal_at else None,
            'confidence_score': self.confidence_score,
            'confidence_label': self.get_confidence_label(),
            'vpn_flag': self.vpn_flag,
            'is_flagged': self.is_flagged()
        }
        
        if include_location:
            data.update({
                'geo_country': self.geo_country,
                'geo_region': self.geo_region,
                'geo_city': self.geo_city,
                'geo_lat': self.geo_lat,
                'geo_lon': self.geo_lon,
                'provider_confidence': self.provider_confidence
            })
        
        if include_sensitive:
            data.update({
                'ip_hash': self.ip_hash,
                'ua': self.ua,
                'accept_language': self.accept_language
            })
        
        return data
    
    def __repr__(self):
        return f'<Message {self.id[:8]}... to {self.slug_owner}>'


class SystemMessageTemplate(db.Model):
    __tablename__ = 'system_message_templates'
    
    id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.Enum('agradavel', 'convite', name='template_categories'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'text': self.text,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<SystemMessageTemplate {self.id}>'


class BannedIP(db.Model):
    __tablename__ = 'banned_ips'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    reason = db.Column(db.Text)
    banned_by = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_hash': self.ip_hash,
            'reason': self.reason,
            'banned_by': self.banned_by,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<BannedIP {self.ip_hash}>'
