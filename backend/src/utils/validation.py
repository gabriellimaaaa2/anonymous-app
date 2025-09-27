import re
from datetime import datetime
from flask import jsonify

class ValidationError(Exception):
    """Exceção para erros de validação"""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)

def validate_request_data(data, required_fields=None, optional_fields=None):
    """Valida dados de requisição"""
    if not data:
        raise ValidationError("Dados não fornecidos")
    
    if required_fields:
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                raise ValidationError(f"Campo '{field}' é obrigatório", field)
    
    # Retornar apenas campos válidos
    valid_fields = (required_fields or []) + (optional_fields or [])
    if valid_fields:
        return {k: v for k, v in data.items() if k in valid_fields}
    
    return data

def validate_email(email):
    """Valida formato de email"""
    if not email:
        return False, "Email é obrigatório"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    if len(email) > 255:
        return False, "Email muito longo"
    
    return True, "Email válido"

def validate_slug(slug):
    """Valida formato de slug"""
    if not slug:
        return False, "Slug é obrigatório"
    
    if len(slug) < 3:
        return False, "Slug deve ter pelo menos 3 caracteres"
    
    if len(slug) > 50:
        return False, "Slug deve ter no máximo 50 caracteres"
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, slug):
        return False, "Slug deve conter apenas letras, números, _ e -"
    
    # Verificar palavras reservadas
    reserved_words = [
        'admin', 'api', 'www', 'mail', 'ftp', 'localhost', 'test',
        'staging', 'dev', 'development', 'prod', 'production',
        'app', 'application', 'system', 'root', 'user', 'users',
        'login', 'signup', 'register', 'auth', 'authentication',
        'dashboard', 'panel', 'control', 'manage', 'management'
    ]
    
    if slug.lower() in reserved_words:
        return False, "Slug não pode usar palavras reservadas"
    
    return True, "Slug válido"

def validate_display_name(name):
    """Valida nome de exibição"""
    if not name:
        return False, "Nome é obrigatório"
    
    if len(name) < 2:
        return False, "Nome deve ter pelo menos 2 caracteres"
    
    if len(name) > 100:
        return False, "Nome deve ter no máximo 100 caracteres"
    
    # Permitir letras, números, espaços e alguns caracteres especiais
    pattern = r'^[a-zA-ZÀ-ÿ0-9\s._-]+$'
    if not re.match(pattern, name):
        return False, "Nome contém caracteres inválidos"
    
    return True, "Nome válido"

def validate_message_text(text):
    """Valida texto de mensagem"""
    if not text:
        return False, "Mensagem não pode estar vazia"
    
    if len(text.strip()) < 1:
        return False, "Mensagem não pode estar vazia"
    
    if len(text) > 5000:
        return False, "Mensagem muito longa (máximo 5000 caracteres)"
    
    # Verificar caracteres de controle maliciosos
    if any(ord(char) < 32 and char not in '\n\r\t' for char in text):
        return False, "Mensagem contém caracteres inválidos"
    
    return True, "Mensagem válida"

def validate_date_of_birth(dob_str):
    """Valida data de nascimento"""
    if not dob_str:
        return False, "Data de nascimento é obrigatória", None
    
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    except ValueError:
        return False, "Formato de data inválido (use YYYY-MM-DD)", None
    
    # Verificar se não é no futuro
    today = datetime.now().date()
    if dob > today:
        return False, "Data de nascimento não pode ser no futuro", None
    
    # Verificar idade mínima (16 anos)
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 16:
        return False, "Você deve ter pelo menos 16 anos", None
    
    # Verificar idade máxima razoável (120 anos)
    if age > 120:
        return False, "Data de nascimento inválida", None
    
    return True, "Data válida", dob

def validate_phone_number(phone):
    """Valida número de telefone (opcional)"""
    if not phone:
        return True, "Telefone válido"  # Opcional
    
    # Remover caracteres não numéricos
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Verificar formato brasileiro
    if len(digits_only) == 11 and digits_only.startswith(('11', '12', '13', '14', '15', '16', '17', '18', '19', '21', '22', '24', '27', '28')):
        return True, "Telefone válido"
    elif len(digits_only) == 10 and digits_only.startswith(('11', '12', '13', '14', '15', '16', '17', '18', '19', '21', '22', '24', '27', '28')):
        return True, "Telefone válido"
    
    return False, "Formato de telefone inválido"

def validate_url(url):
    """Valida URL"""
    if not url:
        return True, "URL válida"  # Opcional
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        return False, "Formato de URL inválido"
    
    if len(url) > 2048:
        return False, "URL muito longa"
    
    return True, "URL válida"

def validate_image_url(url):
    """Valida URL de imagem"""
    is_valid, message = validate_url(url)
    if not is_valid:
        return is_valid, message
    
    if url:
        # Verificar extensões de imagem
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if not any(url.lower().endswith(ext) for ext in valid_extensions):
            return False, "URL deve apontar para uma imagem válida"
    
    return True, "URL de imagem válida"

def validate_pagination(page, per_page, max_per_page=100):
    """Valida parâmetros de paginação"""
    try:
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 20
    except (ValueError, TypeError):
        return False, "Parâmetros de paginação inválidos", 1, 20
    
    if page < 1:
        page = 1
    
    if per_page < 1:
        per_page = 20
    elif per_page > max_per_page:
        per_page = max_per_page
    
    return True, "Paginação válida", page, per_page

def sanitize_search_query(query):
    """Sanitiza query de busca"""
    if not query:
        return ""
    
    # Remover caracteres especiais perigosos
    sanitized = re.sub(r'[<>"\';\\]', '', query)
    
    # Limitar tamanho
    sanitized = sanitized[:200]
    
    return sanitized.strip()

def validate_sort_params(sort_by, sort_order, allowed_fields):
    """Valida parâmetros de ordenação"""
    if sort_by and sort_by not in allowed_fields:
        return False, f"Campo de ordenação inválido. Permitidos: {', '.join(allowed_fields)}", None, None
    
    if sort_order and sort_order.lower() not in ['asc', 'desc']:
        return False, "Ordem deve ser 'asc' ou 'desc'", None, None
    
    sort_by = sort_by or allowed_fields[0] if allowed_fields else 'created_at'
    sort_order = sort_order.lower() if sort_order else 'desc'
    
    return True, "Ordenação válida", sort_by, sort_order

def create_error_response(message, field=None, status_code=400):
    """Cria resposta de erro padronizada"""
    error_data = {'error': message}
    if field:
        error_data['field'] = field
    
    return jsonify(error_data), status_code
