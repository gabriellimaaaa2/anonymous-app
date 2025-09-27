import re
import requests
from flask import current_app
from openai import OpenAI

class ModerationService:
    """Serviço de moderação de conteúdo"""
    
    def __init__(self):
        self.openai_client = None
        self.perspective_api_key = None
    
    def _init_services(self):
        """Inicializa os serviços de moderação"""
        try:
            openai_key = current_app.config.get('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
            
            self.perspective_api_key = current_app.config.get('PERSPECTIVE_API_KEY')
        except RuntimeError:
            # Fora do contexto da aplicação
            self.openai_client = None
            self.perspective_api_key = None
    
    def moderate_message(self, text, user_context=None):
        """
        Modera uma mensagem e retorna resultado da análise
        Retorna: dict com status, confidence, reasons, action
        """
        # Inicializar serviços se ainda não foram inicializados
        if self.openai_client is None and self.perspective_api_key is None:
            self._init_services()
            
        if not text or len(text.strip()) == 0:
            return {
                'status': 'blocked',
                'confidence': 100,
                'reasons': ['Mensagem vazia'],
                'action': 'block'
            }
        
        # Lista de verificações
        checks = []
        
        # 1. Verificação de palavras proibidas
        banned_check = self._check_banned_words(text)
        checks.append(banned_check)
        
        # 2. Verificação de spam/repetição
        spam_check = self._check_spam_patterns(text)
        checks.append(spam_check)
        
        # 3. Verificação de informações pessoais
        pii_check = self._check_personal_info(text)
        checks.append(pii_check)
        
        # 4. Verificação com OpenAI (se disponível)
        if self.openai_client:
            openai_check = self._check_openai_moderation(text)
            checks.append(openai_check)
        
        # 5. Verificação com Perspective API (se disponível)
        if self.perspective_api_key:
            perspective_check = self._check_perspective_api(text)
            checks.append(perspective_check)
        
        # Combinar resultados
        return self._combine_moderation_results(checks)
    
    def _check_banned_words(self, text):
        """Verifica palavras e padrões proibidos"""
        banned_words = [
            # Palavrões e ofensas
            'puta', 'vadia', 'vagabunda', 'piranha', 'cadela',
            'fdp', 'filho da puta', 'filha da puta',
            'merda', 'bosta', 'caralho', 'porra', 'cu',
            'buceta', 'xoxota', 'ppk', 'xereca',
            'viado', 'bicha', 'gay', 'sapatão',
            
            # Ameaças e violência
            'matar', 'morrer', 'suicídio', 'suicidar',
            'estuprar', 'estupro', 'violentar',
            'bater', 'socar', 'agredir',
            
            # Drogas
            'cocaína', 'crack', 'maconha', 'heroína',
            'ecstasy', 'lsd', 'droga', 'tráfico',
            
            # Informações pessoais (padrões)
            'cpf', 'rg', 'telefone', 'celular',
            'endereço', 'casa', 'rua', 'número'
        ]
        
        text_lower = text.lower()
        found_words = []
        
        for word in banned_words:
            if word in text_lower:
                found_words.append(word)
        
        if found_words:
            return {
                'type': 'banned_words',
                'status': 'flagged',
                'confidence': 90,
                'reasons': [f"Palavras proibidas: {', '.join(found_words)}"],
                'severity': 'high' if any(w in ['matar', 'estuprar', 'suicídio'] for w in found_words) else 'medium'
            }
        
        return {
            'type': 'banned_words',
            'status': 'approved',
            'confidence': 95,
            'reasons': [],
            'severity': 'none'
        }
    
    def _check_spam_patterns(self, text):
        """Verifica padrões de spam"""
        # Verificar repetição excessiva de caracteres
        if re.search(r'(.)\1{10,}', text):
            return {
                'type': 'spam',
                'status': 'flagged',
                'confidence': 80,
                'reasons': ['Repetição excessiva de caracteres'],
                'severity': 'low'
            }
        
        # Verificar muitas maiúsculas
        if len(text) > 20 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
            return {
                'type': 'spam',
                'status': 'flagged',
                'confidence': 60,
                'reasons': ['Excesso de letras maiúsculas'],
                'severity': 'low'
            }
        
        # Verificar URLs suspeitas
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        if urls:
            return {
                'type': 'spam',
                'status': 'flagged',
                'confidence': 70,
                'reasons': ['Contém URLs'],
                'severity': 'medium'
            }
        
        return {
            'type': 'spam',
            'status': 'approved',
            'confidence': 90,
            'reasons': [],
            'severity': 'none'
        }
    
    def _check_personal_info(self, text):
        """Verifica informações pessoais"""
        patterns = {
            'cpf': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
            'telefone': r'(?:\+55\s?)?(?:\(\d{2}\)\s?)?\d{4,5}-?\d{4}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'cep': r'\d{5}-?\d{3}'
        }
        
        found_patterns = []
        for name, pattern in patterns.items():
            if re.search(pattern, text):
                found_patterns.append(name)
        
        if found_patterns:
            return {
                'type': 'personal_info',
                'status': 'flagged',
                'confidence': 95,
                'reasons': [f"Informações pessoais detectadas: {', '.join(found_patterns)}"],
                'severity': 'high'
            }
        
        return {
            'type': 'personal_info',
            'status': 'approved',
            'confidence': 95,
            'reasons': [],
            'severity': 'none'
        }
    
    def _check_openai_moderation(self, text):
        """Verifica com OpenAI Moderation API"""
        try:
            response = self.openai_client.moderations.create(input=text)
            result = response.results[0]
            
            if result.flagged:
                categories = [cat for cat, flagged in result.categories.__dict__.items() if flagged]
                return {
                    'type': 'openai',
                    'status': 'flagged',
                    'confidence': 85,
                    'reasons': [f"OpenAI detectou: {', '.join(categories)}"],
                    'severity': 'high' if any(cat in ['violence', 'self-harm'] for cat in categories) else 'medium'
                }
            
            return {
                'type': 'openai',
                'status': 'approved',
                'confidence': 90,
                'reasons': [],
                'severity': 'none'
            }
            
        except Exception as e:
            current_app.logger.warning(f"Erro na moderação OpenAI: {e}")
            return {
                'type': 'openai',
                'status': 'approved',
                'confidence': 50,
                'reasons': ['Erro na verificação OpenAI'],
                'severity': 'none'
            }
    
    def _check_perspective_api(self, text):
        """Verifica com Google Perspective API"""
        try:
            url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={self.perspective_api_key}"
            
            data = {
                'comment': {'text': text},
                'requestedAttributes': {
                    'TOXICITY': {},
                    'SEVERE_TOXICITY': {},
                    'IDENTITY_ATTACK': {},
                    'INSULT': {},
                    'PROFANITY': {},
                    'THREAT': {}
                }
            }
            
            response = requests.post(url, json=data, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            scores = result['attributeScores']
            
            # Verificar se algum score está acima do threshold
            high_scores = []
            for attribute, data in scores.items():
                score = data['summaryScore']['value']
                if score > 0.7:  # Threshold de 70%
                    high_scores.append(f"{attribute}: {score:.2f}")
            
            if high_scores:
                return {
                    'type': 'perspective',
                    'status': 'flagged',
                    'confidence': 80,
                    'reasons': [f"Perspective API detectou: {', '.join(high_scores)}"],
                    'severity': 'medium'
                }
            
            return {
                'type': 'perspective',
                'status': 'approved',
                'confidence': 85,
                'reasons': [],
                'severity': 'none'
            }
            
        except Exception as e:
            current_app.logger.warning(f"Erro na Perspective API: {e}")
            return {
                'type': 'perspective',
                'status': 'approved',
                'confidence': 50,
                'reasons': ['Erro na verificação Perspective'],
                'severity': 'none'
            }
    
    def _combine_moderation_results(self, checks):
        """Combina resultados de múltiplas verificações"""
        flagged_checks = [check for check in checks if check['status'] == 'flagged']
        
        if not flagged_checks:
            return {
                'status': 'approved',
                'confidence': min([check['confidence'] for check in checks]),
                'reasons': [],
                'action': 'approve'
            }
        
        # Determinar severidade máxima
        max_severity = 'none'
        for check in flagged_checks:
            if check['severity'] == 'high':
                max_severity = 'high'
                break
            elif check['severity'] == 'medium' and max_severity != 'high':
                max_severity = 'medium'
            elif check['severity'] == 'low' and max_severity == 'none':
                max_severity = 'low'
        
        # Determinar ação baseada na severidade
        if max_severity == 'high':
            action = 'block'
            status = 'blocked'
        elif max_severity == 'medium':
            action = 'flag'
            status = 'flagged'
        else:
            action = 'flag'
            status = 'flagged'
        
        # Combinar razões
        all_reasons = []
        for check in flagged_checks:
            all_reasons.extend(check['reasons'])
        
        # Calcular confiança média dos checks que flagaram
        avg_confidence = sum([check['confidence'] for check in flagged_checks]) / len(flagged_checks)
        
        return {
            'status': status,
            'confidence': int(avg_confidence),
            'reasons': all_reasons,
            'action': action,
            'severity': max_severity
        }

# Instância global do serviço
moderation_service = ModerationService()

def moderate_content(text, user_context=None):
    """Função helper para moderar conteúdo"""
    return moderation_service.moderate_message(text, user_context)
