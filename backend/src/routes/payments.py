import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src.models import db
from src.models.user import User
from src.models.message import Message
from src.models.payment import Payment, RevealLog, IPVault
from src.utils.security import get_client_ip, decrypt_ip
from src.utils.validation import validate_request_data
from src.utils.geoip import get_location_for_ip

payments_bp = Blueprint('payments', __name__)

# Rate limiting para rotas de pagamento
limiter = Limiter(
    key_func=lambda: get_client_ip(request),
    default_limits=["100 per hour", "10 per minute"]
)

@payments_bp.route('/packages', methods=['GET'])
@jwt_required()
def get_credit_packages():
    """Obtém pacotes de créditos disponíveis"""
    try:
        packages = [
            {
                'id': 'credits_5',
                'name': '5 Créditos',
                'credits': 5,
                'price_brl': 4.99,
                'price_usd': 0.99,
                'popular': False,
                'description': 'Ideal para começar'
            },
            {
                'id': 'credits_15',
                'name': '15 Créditos',
                'credits': 15,
                'price_brl': 12.99,
                'price_usd': 2.49,
                'popular': True,
                'description': 'Mais popular',
                'bonus': 2  # 2 créditos extras
            },
            {
                'id': 'credits_50',
                'name': '50 Créditos',
                'credits': 50,
                'price_brl': 39.99,
                'price_usd': 7.99,
                'popular': False,
                'description': 'Melhor valor',
                'bonus': 10  # 10 créditos extras
            },
            {
                'id': 'credits_100',
                'name': '100 Créditos',
                'credits': 100,
                'price_brl': 69.99,
                'price_usd': 13.99,
                'popular': False,
                'description': 'Para usuários avançados',
                'bonus': 25  # 25 créditos extras
            }
        ]
        
        return jsonify({'packages': packages}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter pacotes: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@payments_bp.route('/create-payment', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def create_payment():
    """Cria um pagamento para compra de créditos"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        # Validar dados de entrada
        required_fields = ['package_id', 'payment_method']
        data = validate_request_data(request.json, required_fields)
        
        # Validar método de pagamento
        if data['payment_method'] not in ['pix', 'credit_card']:
            return jsonify({'error': 'Método de pagamento inválido'}), 400
        
        # Buscar pacote
        packages = {
            'credits_5': {'credits': 5, 'price_brl': 4.99, 'bonus': 0},
            'credits_15': {'credits': 15, 'price_brl': 12.99, 'bonus': 2},
            'credits_50': {'credits': 50, 'price_brl': 39.99, 'bonus': 10},
            'credits_100': {'credits': 100, 'price_brl': 69.99, 'bonus': 25}
        }
        
        package = packages.get(data['package_id'])
        if not package:
            return jsonify({'error': 'Pacote não encontrado'}), 404
        
        # Criar pagamento
        payment = Payment(
            user_id=user.id,
            package_id=data['package_id'],
            credits_amount=package['credits'] + package['bonus'],
            amount_brl=package['price_brl'],
            payment_method=data['payment_method'],
            status='pending'
        )
        
        db.session.add(payment)
        db.session.flush()  # Para obter o ID
        
        # Gerar dados específicos do método de pagamento
        if data['payment_method'] == 'pix':
            payment_data = generate_pix_payment(payment)
        else:
            payment_data = generate_card_payment(payment, data.get('card_data'))
        
        payment.external_id = payment_data.get('external_id')
        payment.payment_data = payment_data
        
        db.session.commit()
        
        return jsonify({
            'payment': payment.to_dict(),
            'payment_data': payment_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar pagamento: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


def generate_pix_payment(payment):
    """Gera dados para pagamento PIX"""
    # Simular integração com gateway de pagamento (ex: Mercado Pago, PagSeguro)
    pix_code = f"00020126580014BR.GOV.BCB.PIX0136{uuid.uuid4()}5204000053039865802BR5925ANONYMOUS PAGAMENTOS LTDA6009SAO PAULO62070503***6304"
    
    # Hash do código PIX para verificação
    pix_hash = hashlib.sha256(pix_code.encode()).hexdigest()[:16]
    
    return {
        'external_id': f"pix_{payment.id}_{pix_hash}",
        'pix_code': pix_code,
        'qr_code_url': f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",  # Placeholder
        'expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
        'instructions': [
            "Abra o app do seu banco",
            "Escaneie o código QR ou copie o código PIX",
            "Confirme o pagamento",
            "Seus créditos serão adicionados automaticamente"
        ]
    }


def generate_card_payment(payment, card_data):
    """Gera dados para pagamento com cartão"""
    # Simular integração com Stripe ou similar
    return {
        'external_id': f"card_{payment.id}_{uuid.uuid4().hex[:8]}",
        'client_secret': f"pi_{uuid.uuid4().hex}_secret_{uuid.uuid4().hex[:8]}",
        'publishable_key': current_app.config.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...'),
        'amount': int(payment.amount_brl * 100),  # Centavos
        'currency': 'brl'
    }


@payments_bp.route('/webhook/pix', methods=['POST'])
@limiter.limit("100 per minute")
def pix_webhook():
    """Webhook para confirmação de pagamento PIX"""
    try:
        # Validar assinatura do webhook
        signature = request.headers.get('X-Signature')
        if not validate_webhook_signature(request.data, signature):
            return jsonify({'error': 'Assinatura inválida'}), 401
        
        data = request.json
        external_id = data.get('external_id')
        status = data.get('status')
        
        if not external_id or not status:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        # Buscar pagamento
        payment = Payment.query.filter_by(external_id=external_id).first()
        if not payment:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        
        # Atualizar status
        if status == 'approved' and payment.status == 'pending':
            payment.status = 'completed'
            payment.completed_at = datetime.utcnow()
            
            # Adicionar créditos ao usuário
            user = User.query.get(payment.user_id)
            if user:
                user.reveal_credits += payment.credits_amount
                user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            current_app.logger.info(f"Pagamento {payment.id} confirmado - {payment.credits_amount} créditos adicionados ao usuário {user.id}")
        
        elif status in ['cancelled', 'failed']:
            payment.status = status
            db.session.commit()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no webhook PIX: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@payments_bp.route('/webhook/stripe', methods=['POST'])
@limiter.limit("100 per minute")
def stripe_webhook():
    """Webhook para confirmação de pagamento Stripe"""
    try:
        import stripe
        
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            return jsonify({'error': 'Payload inválido'}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({'error': 'Assinatura inválida'}), 400
        
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            external_id = payment_intent.get('metadata', {}).get('payment_id')
            
            if external_id:
                payment = Payment.query.filter_by(external_id=external_id).first()
                if payment and payment.status == 'pending':
                    payment.status = 'completed'
                    payment.completed_at = datetime.utcnow()
                    
                    # Adicionar créditos ao usuário
                    user = User.query.get(payment.user_id)
                    if user:
                        user.reveal_credits += payment.credits_amount
                        user.updated_at = datetime.utcnow()
                    
                    db.session.commit()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no webhook Stripe: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@payments_bp.route('/reveal/<message_id>', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def reveal_message_location(message_id):
    """Revela a localização de uma mensagem usando créditos"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.is_banned:
            return jsonify({'error': 'Usuário não encontrado ou banido'}), 404
        
        # Verificar se tem créditos suficientes
        if user.reveal_credits < 1:
            return jsonify({'error': 'Créditos insuficientes'}), 400
        
        # Buscar mensagem
        message = Message.query.filter_by(
            id=message_id,
            slug_owner=user.slug
        ).first()
        
        if not message:
            return jsonify({'error': 'Mensagem não encontrada'}), 404
        
        # Verificar se já foi revelada
        existing_reveal = RevealLog.query.filter_by(
            message_id=message.id,
            user_id=user.id
        ).first()
        
        if existing_reveal:
            return jsonify({'error': 'Localização já foi revelada'}), 400
        
        # Verificar se pode ser revelada
        can_reveal, reveal_message = message.can_be_revealed(user)
        if not can_reveal:
            return jsonify({'error': reveal_message}), 400
        
        # Obter IP real da mensagem
        ip_vault = IPVault.query.filter_by(message_id=message.id).first()
        if not ip_vault:
            return jsonify({'error': 'Dados de localização não disponíveis'}), 404
        
        try:
            real_ip = decrypt_ip(ip_vault.ip_encrypted, ip_vault.salt)
        except Exception:
            return jsonify({'error': 'Erro ao descriptografar dados de localização'}), 500
        
        # Obter localização mais precisa
        from src.utils.geoip import geoip_service
        precise_location = geoip_service.get_location_info(real_ip)
        
        # Consumir crédito
        user.reveal_credits -= 1
        user.updated_at = datetime.utcnow()
        
        # Criar log de revelação
        reveal_log = RevealLog(
            message_id=message.id,
            user_id=user.id,
            credits_used=1,
            ip_revealed=real_ip,
            city=precise_location.get('city'),
            region=precise_location.get('region'),
            country=precise_location.get('country'),
            latitude=precise_location.get('lat'),
            longitude=precise_location.get('lon'),
            confidence_score=precise_location.get('confidence', 0),
            provider_used='maxmind_premium'
        )
        
        db.session.add(reveal_log)
        
        # Incrementar contador de revelações da mensagem
        message.reveal_count += 1
        
        db.session.commit()
        
        current_app.logger.info(f"Localização revelada - Usuário: {user.id}, Mensagem: {message.id[:8]}...")
        
        return jsonify({
            'message': 'Localização revelada com sucesso!',
            'reveal_details': reveal_log.to_dict(),
            'remaining_credits': user.reveal_credits
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao revelar localização: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@payments_bp.route('/payment-status/<payment_id>', methods=['GET'])
@jwt_required()
def get_payment_status(payment_id):
    """Obtém status de um pagamento"""
    try:
        user_id = get_jwt_identity()
        
        payment = Payment.query.filter_by(
            id=payment_id,
            user_id=user_id
        ).first()
        
        if not payment:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        
        return jsonify({
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter status do pagamento: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@payments_bp.route('/history', methods=['GET'])
@jwt_required()
def get_payment_history():
    """Obtém histórico de pagamentos do usuário"""
    try:
        user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        
        payments = Payment.query.filter_by(user_id=user_id).order_by(
            Payment.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments.items],
            'pagination': {
                'page': payments.page,
                'per_page': payments.per_page,
                'total': payments.total,
                'pages': payments.pages,
                'has_next': payments.has_next,
                'has_prev': payments.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter histórico de pagamentos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@payments_bp.route('/reveals', methods=['GET'])
@jwt_required()
def get_reveal_history():
    """Obtém histórico de revelações do usuário"""
    try:
        user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        
        reveals = RevealLog.query.filter_by(user_id=user_id).order_by(
            RevealLog.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'reveals': [reveal.to_dict() for reveal in reveals.items],
            'pagination': {
                'page': reveals.page,
                'per_page': reveals.per_page,
                'total': reveals.total,
                'pages': reveals.pages,
                'has_next': reveals.has_next,
                'has_prev': reveals.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter histórico de revelações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


def validate_webhook_signature(payload, signature):
    """Valida assinatura do webhook"""
    try:
        webhook_secret = current_app.config.get('WEBHOOK_SECRET', 'default_secret')
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False
