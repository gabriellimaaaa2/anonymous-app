import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    provider = db.Column(db.Enum('stripe', 'pix', 'pagar_me', 'gerencianet', name='payment_providers'), nullable=False)
    provider_payment_id = db.Column(db.String(100))
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), default='BRL')
    status = db.Column(db.Enum('pending', 'completed', 'failed', 'refunded', name='payment_statuses'), default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    payment_metadata = db.Column(db.JSON)
    
    def mark_completed(self):
        """Marca o pagamento como concluído"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self):
        """Marca o pagamento como falhado"""
        self.status = 'failed'
    
    def mark_refunded(self):
        """Marca o pagamento como reembolsado"""
        self.status = 'refunded'
    
    def get_amount_real(self):
        """Retorna o valor em reais"""
        return self.amount_cents / 100
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'provider_payment_id': self.provider_payment_id,
            'amount_cents': self.amount_cents,
            'amount_real': self.get_amount_real(),
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'payment_metadata': self.payment_metadata
        }
    
    def __repr__(self):
        return f'<Payment {self.id[:8]}... {self.provider} {self.get_amount_real():.2f}>'


class RevealLog(db.Model):
    __tablename__ = 'reveal_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    payment_provider = db.Column(db.String(20))
    payment_id = db.Column(db.String(100))
    amount_cents = db.Column(db.Integer, nullable=False)
    city = db.Column(db.String(100))
    region = db.Column(db.String(100))
    confidence_score = db.Column(db.Integer)
    map_geojson = db.Column(db.JSON)
    notes = db.Column(db.Text)
    
    def get_amount_real(self):
        """Retorna o valor em reais"""
        return self.amount_cents / 100
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'payment_provider': self.payment_provider,
            'payment_id': self.payment_id,
            'amount_cents': self.amount_cents,
            'amount_real': self.get_amount_real(),
            'city': self.city,
            'region': self.region,
            'confidence_score': self.confidence_score,
            'map_geojson': self.map_geojson,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<RevealLog {self.id[:8]}... {self.city}>'


class IPVault(db.Model):
    """Tabela para armazenar IPs encriptados com acesso restrito"""
    __tablename__ = 'ip_vault'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = db.Column(db.String(36), nullable=False, unique=True)
    ip_encrypted = db.Column(db.Text, nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_encrypted=False):
        data = {
            'id': self.id,
            'message_id': self.message_id,
            'created_at': self.created_at.isoformat()
        }
        
        if include_encrypted:
            data.update({
                'ip_encrypted': self.ip_encrypted,
                'salt': self.salt
            })
        
        return data
    
    def __repr__(self):
        return f'<IPVault {self.id[:8]}... for message {self.message_id[:8]}...>'
