import os
import requests
import geoip2.database
import geoip2.errors
from flask import current_app

class GeoIPService:
    """Serviço para obter informações de localização por IP"""
    
    def __init__(self):
        self.maxmind_db_path = None
        self.ipinfo_token = None
    
    def _init_services(self):
        """Inicializa os serviços de GeoIP"""
        try:
            self.maxmind_db_path = current_app.config.get('MAXMIND_DB_PATH')
            self.ipinfo_token = current_app.config.get('IPINFO_TOKEN')
        except RuntimeError:
            # Fora do contexto da aplicação, usar valores padrão
            self.maxmind_db_path = None
            self.ipinfo_token = None
    
    def get_location_info(self, ip_address):
        """
        Obtém informações de localização para um IP
        Retorna: dict com country, region, city, lat, lon, confidence, vpn_flag
        """
        # Inicializar serviços se ainda não foram inicializados
        if self.maxmind_db_path is None and self.ipinfo_token is None:
            self._init_services()
            
        if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
            return self._get_default_location()
        
        # Tentar MaxMind primeiro
        location = self._get_maxmind_location(ip_address)
        if location:
            return location
        
        # Fallback para IPInfo
        location = self._get_ipinfo_location(ip_address)
        if location:
            return location
        
        # Retornar localização padrão se nada funcionar
        return self._get_default_location()
    
    def _get_maxmind_location(self, ip_address):
        """Obtém localização usando MaxMind GeoLite2"""
        if not self.maxmind_db_path or not os.path.exists(self.maxmind_db_path):
            return None
        
        try:
            with geoip2.database.Reader(self.maxmind_db_path) as reader:
                response = reader.city(ip_address)
                
                return {
                    'country': response.country.iso_code,
                    'region': response.subdivisions.most_specific.name or response.subdivisions.most_specific.iso_code,
                    'city': response.city.name,
                    'lat': float(response.location.latitude) if response.location.latitude else None,
                    'lon': float(response.location.longitude) if response.location.longitude else None,
                    'confidence': response.location.accuracy_radius or 50,
                    'vpn_flag': False,  # MaxMind não detecta VPN na versão gratuita
                    'provider': 'maxmind'
                }
        except (geoip2.errors.AddressNotFoundError, geoip2.errors.GeoIP2Error, Exception) as e:
            current_app.logger.warning(f"Erro MaxMind para IP {ip_address}: {e}")
            return None
    
    def _get_ipinfo_location(self, ip_address):
        """Obtém localização usando IPInfo.io"""
        if not self.ipinfo_token:
            return None
        
        try:
            url = f"https://ipinfo.io/{ip_address}/json"
            headers = {'Authorization': f'Bearer {self.ipinfo_token}'}
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar se é VPN/Proxy
            vpn_flag = False
            if 'privacy' in data:
                privacy = data['privacy']
                vpn_flag = privacy.get('vpn', False) or privacy.get('proxy', False) or privacy.get('tor', False)
            
            # Extrair coordenadas
            lat, lon = None, None
            if 'loc' in data:
                try:
                    lat_str, lon_str = data['loc'].split(',')
                    lat, lon = float(lat_str), float(lon_str)
                except (ValueError, AttributeError):
                    pass
            
            return {
                'country': data.get('country'),
                'region': data.get('region'),
                'city': data.get('city'),
                'lat': lat,
                'lon': lon,
                'confidence': 70,  # IPInfo geralmente tem boa precisão
                'vpn_flag': vpn_flag,
                'provider': 'ipinfo'
            }
            
        except (requests.RequestException, ValueError, KeyError) as e:
            current_app.logger.warning(f"Erro IPInfo para IP {ip_address}: {e}")
            return None
    
    def _get_default_location(self):
        """Retorna localização padrão para IPs locais ou quando falha"""
        return {
            'country': 'BR',
            'region': 'São Paulo',
            'city': 'São Paulo',
            'lat': -23.5505,
            'lon': -46.6333,
            'confidence': 0,
            'vpn_flag': False,
            'provider': 'default'
        }
    
    def is_vpn_detected(self, ip_address):
        """Verifica especificamente se o IP é VPN/Proxy"""
        location = self.get_location_info(ip_address)
        return location.get('vpn_flag', False)
    
    def calculate_confidence_score(self, location_data, timezone_match=False, language_match=False, history_score=0):
        """
        Calcula score de confiança baseado em múltiplos fatores
        """
        provider_confidence = location_data.get('confidence', 0)
        vpn_flag = location_data.get('vpn_flag', False)
        
        # Fórmula de confiança
        confidence = int(provider_confidence * 0.5)
        
        if timezone_match:
            confidence += 15
        
        if language_match:
            confidence += 10
        
        confidence += min(15, history_score * 5)
        
        if vpn_flag:
            confidence -= 30
        
        # Garantir que está entre 0 e 100
        confidence = max(0, min(100, confidence))
        
        return confidence
    
    def get_confidence_label(self, confidence_score):
        """Retorna label da confiança"""
        if confidence_score >= 80:
            return 'ALTA'
        elif confidence_score >= 50:
            return 'MÉDIA'
        else:
            return 'BAIXA'

# Instância global do serviço
geoip_service = GeoIPService()

def get_location_for_ip(ip_address):
    """Função helper para obter localização"""
    return geoip_service.get_location_info(ip_address)

def detect_vpn(ip_address):
    """Função helper para detectar VPN"""
    return geoip_service.is_vpn_detected(ip_address)

def calculate_location_confidence(location_data, **kwargs):
    """Função helper para calcular confiança"""
    return geoip_service.calculate_confidence_score(location_data, **kwargs)
