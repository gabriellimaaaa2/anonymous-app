import os
import sys
from datetime import datetime, timedelta
import random

# Adicionar o diretório raiz do backend ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from main import create_app
from models import db
from models.user import User
from models.message import Message
from models.payment import Payment, RevealLog, IPVault
from models.admin import AdminUser, AdminAuditLog, ModerationQueue, SystemConfig
from utils.security import encrypt_ip

def seed_data():
    app = create_app("development")
    with app.app_context():
        print("\n--- Iniciando o processo de seed de dados ---")

        # Limpar dados existentes (opcional, para testes)
        print("Limpando tabelas existentes...")
        db.drop_all()
        db.create_all()
        print("Tabelas recriadas.")

        # 1. Criar Usuários
        print("Criando usuários...")
        user1 = User(email="user1@example.com", display_name="Alice", slug="alice")
        user1.set_password("Password123!")
        user1.is_verified = True
        user1.reveal_credits = 10
        db.session.add(user1)

        user2 = User(email="user2@example.com", display_name="Bob", slug="bob")
        user2.set_password("Password123!")
        user2.is_verified = True
        user2.reveal_credits = 5
        db.session.add(user2)

        user3 = User(email="user3@example.com", display_name="Charlie", slug="charlie")
        user3.set_password("Password123!")
        user3.is_verified = True
        db.session.add(user3)

        # Criar um usuário admin
        admin_user = User(email="admin@example.com", display_name="Admin", slug="admin")
        admin_user.set_password("AdminPassword123!")
        admin_user.is_verified = True
        db.session.add(admin_user)
        db.session.flush() # Para obter o ID do usuário antes do commit

        admin_role = AdminUser(user_id=admin_user.id, role="super_admin", is_active=True)
        db.session.add(admin_role)

        db.session.commit()
        print("Usuários e Admin criados.")

        # 2. Criar Mensagens
        print("Criando mensagens...")
        messages_data = [
            {"text": "Olá Alice, você é incrível!", "slug_owner": user1.slug, "ip_address": "192.168.1.1", "country": "Brazil", "city": "Sao Paulo"},
            {"text": "Qual seu filme favorito, Alice?", "slug_owner": user1.slug, "ip_address": "187.1.2.3", "country": "Brazil", "city": "Rio de Janeiro"},
            {"text": "Bob, me conta um segredo...", "slug_owner": user2.slug, "ip_address": "200.200.200.200", "country": "Argentina", "city": "Buenos Aires"},
            {"text": "Você é uma inspiração, Charlie!", "slug_owner": user3.slug, "ip_address": "1.1.1.1", "country": "USA", "city": "New York"},
            {"text": "Mensagem de teste para moderação. Conteúdo impróprio aqui.", "slug_owner": user1.slug, "ip_address": "10.0.0.1", "country": "Brazil", "city": "Belo Horizonte", "moderation_status": "pending"},
        ]

        for msg_data in messages_data:
            encrypted_ip, ip_salt = encrypt_ip(msg_data["ip_address"])
            message = Message(
                text=msg_data["text"],
                slug_owner=msg_data["slug_owner"],
                ip_hash=encrypted_ip,
                ip_salt=ip_salt,
                country=msg_data["country"],
                city=msg_data["city"],
                moderation_status=msg_data.get("moderation_status", "approved")
            )
            db.session.add(message)
        db.session.commit()
        print("Mensagens criadas.")

        # 3. Criar Pagamentos e Revelações
        print("Criando pagamentos e revelações...")
        payment1 = Payment(user_id=user1.id, amount=20.00, currency="BRL", status="completed", payment_method="PIX", transaction_id="pix_123")
        db.session.add(payment1)
        db.session.commit()

        # Revelar uma mensagem
        message_to_reveal = Message.query.filter_by(slug_owner=user1.slug).first()
        if message_to_reveal:
            reveal_log = RevealLog(user_id=user1.id, message_id=message_to_reveal.id, cost=1)
            db.session.add(reveal_log)
            db.session.commit()
            print(f"Mensagem {message_to_reveal.id} revelada por {user1.email}.")

        # 4. Criar Logs de Auditoria e Fila de Moderação
        print("Criando logs de auditoria e fila de moderação...")
        admin_audit = AdminAuditLog(admin_id=admin_user.id, action="user_created", target_type="User", target_id=user1.id, details="Created user Alice")
        db.session.add(admin_audit)

        pending_message = Message.query.filter_by(moderation_status="pending").first()
        if pending_message:
            mod_queue = ModerationQueue(message_id=pending_message.id, reason="Conteúdo potencialmente impróprio")
            db.session.add(mod_queue)

        # 5. Configurações do Sistema
        print("Criando configurações do sistema...")
        config_item = SystemConfig(key="min_reveal_credits", value="1")
        db.session.add(config_item)
        config_item2 = SystemConfig(key="welcome_message", value="Bem-vindo ao Anonymous!")
        db.session.add(config_item2)

        db.session.commit()
        print("Logs de auditoria, fila de moderação e configurações criados.")

        print("--- Processo de seed de dados concluído com sucesso! ---")

if __name__ == "__main__":
    seed_data()
