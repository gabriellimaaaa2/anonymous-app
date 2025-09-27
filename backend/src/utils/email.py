import os
from flask import current_app, render_template_string
from flask_mail import Mail, Message
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

mail = Mail()

def init_mail(app):
    """Inicializa o sistema de email"""
    mail.init_app(app)
    return mail

def send_email(to, subject, template=None, **kwargs):
    """Envia email usando template"""
    try:
        # Se não tiver configuração SMTP, simular envio
        if not current_app.config.get('MAIL_USERNAME'):
            current_app.logger.info(f"Email simulado para {to}: {subject}")
            return True
        
        # Obter template de email
        html_content = get_email_template(template, **kwargs)
        
        # Criar mensagem
        msg = Message(
            subject=subject,
            recipients=[to],
            html=html_content,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Enviar
        mail.send(msg)
        current_app.logger.info(f"Email enviado para {to}: {subject}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar email para {to}: {e}")
        return False

def get_email_template(template_name, **kwargs):
    """Obtém template de email"""
    templates = {
        'verify_email': """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verificar Email - ANONYMOUS</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #000 0%, #333 100%); color: #FFD700; padding: 30px; text-align: center; }
                .logo { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
                .content { background: #f9f9f9; padding: 30px; }
                .button { display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
                .footer { background: #333; color: #ccc; padding: 20px; text-align: center; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">ANONYMOUS</div>
                    <p>Bem-vindo ao mundo das mensagens anônimas</p>
                </div>
                <div class="content">
                    <h2>Olá, {{ user.display_name }}!</h2>
                    <p>Obrigado por se cadastrar no ANONYMOUS. Para ativar sua conta e começar a receber mensagens anônimas, clique no botão abaixo:</p>
                    <p style="text-align: center;">
                        <a href="{{ verification_url }}" class="button">Verificar Email</a>
                    </p>
                    <p>Ou copie e cole este link no seu navegador:</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 3px;">{{ verification_url }}</p>
                    <p><strong>Este link expira em 24 horas.</strong></p>
                    <p>Se você não se cadastrou no ANONYMOUS, pode ignorar este email.</p>
                </div>
                <div class="footer">
                    <p>© 2024 ANONYMOUS. Todos os direitos reservados.</p>
                    <p>Este é um email automático, não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        
        'reset_password': """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Recuperar Senha - ANONYMOUS</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #000 0%, #333 100%); color: #FFD700; padding: 30px; text-align: center; }
                .logo { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
                .content { background: #f9f9f9; padding: 30px; }
                .button { display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
                .footer { background: #333; color: #ccc; padding: 20px; text-align: center; font-size: 0.9em; }
                .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">ANONYMOUS</div>
                    <p>Recuperação de senha</p>
                </div>
                <div class="content">
                    <h2>Olá, {{ user.display_name }}!</h2>
                    <p>Recebemos uma solicitação para redefinir a senha da sua conta ANONYMOUS.</p>
                    <p style="text-align: center;">
                        <a href="{{ reset_url }}" class="button">Redefinir Senha</a>
                    </p>
                    <p>Ou copie e cole este link no seu navegador:</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 3px;">{{ reset_url }}</p>
                    <div class="warning">
                        <strong>⚠️ Importante:</strong>
                        <ul>
                            <li>Este link expira em 1 hora</li>
                            <li>Só pode ser usado uma vez</li>
                            <li>Se você não solicitou esta recuperação, ignore este email</li>
                        </ul>
                    </div>
                    <p>Por segurança, certifique-se de criar uma senha forte com pelo menos 10 caracteres, incluindo letras maiúsculas, minúsculas, números e símbolos.</p>
                </div>
                <div class="footer">
                    <p>© 2024 ANONYMOUS. Todos os direitos reservados.</p>
                    <p>Este é um email automático, não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        
        'welcome': """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Bem-vindo ao ANONYMOUS</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #000 0%, #333 100%); color: #FFD700; padding: 30px; text-align: center; }
                .logo { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
                .content { background: #f9f9f9; padding: 30px; }
                .button { display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
                .footer { background: #333; color: #ccc; padding: 20px; text-align: center; font-size: 0.9em; }
                .feature { background: white; padding: 20px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #FFD700; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">ANONYMOUS</div>
                    <p>Sua conta foi ativada com sucesso!</p>
                </div>
                <div class="content">
                    <h2>Parabéns, {{ user.display_name }}! 🎉</h2>
                    <p>Sua conta ANONYMOUS está pronta para uso. Agora você pode:</p>
                    
                    <div class="feature">
                        <h3>📨 Receber mensagens anônimas</h3>
                        <p>Compartilhe seu link personalizado e comece a receber mensagens:</p>
                        <p><strong>{{ app_url }}/{{ user.slug }}</strong></p>
                    </div>
                    
                    <div class="feature">
                        <h3>🔍 Descobrir origens</h3>
                        <p>Use revelações para descobrir a cidade/região de quem enviou as mensagens.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>📱 Compartilhar no Instagram</h3>
                        <p>Crie stories personalizados para suas respostas e aumente o engajamento.</p>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{{ app_url }}/dashboard" class="button">Acessar Dashboard</a>
                    </p>
                    
                    <p><strong>Dicas para começar:</strong></p>
                    <ul>
                        <li>Compartilhe seu link no Instagram Stories</li>
                        <li>Adicione o link na sua bio</li>
                        <li>Responda às mensagens para manter o engajamento</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>© 2024 ANONYMOUS. Todos os direitos reservados.</p>
                    <p>Precisa de ajuda? Visite nossa central de suporte.</p>
                </div>
            </div>
        </body>
        </html>
        """
    }
    
    template = templates.get(template_name, templates['verify_email'])
    
    # Adicionar variáveis padrão
    kwargs.update({
        'app_url': current_app.config.get('APP_URL', 'http://localhost:3000'),
        'app_name': current_app.config.get('APP_NAME', 'ANONYMOUS')
    })
    
    return render_template_string(template, **kwargs)

def send_notification_email(to, subject, message, priority='normal'):
    """Envia email de notificação simples"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #333; color: #FFD700; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .footer {{ background: #333; color: #ccc; padding: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ANONYMOUS</h1>
                </div>
                <div class="content">
                    <h2>{subject}</h2>
                    <p>{message}</p>
                </div>
                <div class="footer">
                    <p>© 2024 ANONYMOUS. Todos os direitos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=f"[ANONYMOUS] {subject}",
            recipients=[to],
            html=html_content,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar notificação para {to}: {e}")
        return False

def send_admin_alert(subject, message, details=None):
    """Envia alerta para administradores"""
    admin_email = current_app.config.get('ADMIN_EMAIL')
    if not admin_email:
        return False
    
    full_message = message
    if details:
        full_message += f"\n\nDetalhes:\n{details}"
    
    return send_notification_email(
        to=admin_email,
        subject=f"[ALERTA] {subject}",
        message=full_message,
        priority='high'
    )
