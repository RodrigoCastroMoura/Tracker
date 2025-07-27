import os
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv(dotenv_path="../.env")

class Config:
    """Configuration class for GV50 tracker service"""
    
    # Service Configuration - do .env
    SERVER_ENABLED: bool = os.getenv('SERVER_ENABLED', 'true').lower() == 'true'
    SERVER_IP: str = os.getenv('SERVER_IP', '0.0.0.0')
    SERVER_PORT: int = int(os.getenv('SERVER_PORT', '8000'))  # GV50 devices connect on port 8000
    
    # IP Management - do .env
    ALLOWED_IPS: List[str] = [ip.strip() for ip in os.getenv('ALLOWED_IPS', '').split(',') if ip.strip()]
    
    # Logging Configuration - do .env
    LOGGING_ENABLED: bool = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'
    
    # Database Configuration - do .env
    MONGODB_URI: str = os.getenv('MONGODB_URI', '')
    DATABASE_NAME: str = os.getenv('DATABASE_NAME', 'track')  # Use 'track' where data exists
    
    # Protocol Configuration - do .env
    DEFAULT_PASSWORD: str = os.getenv('DEFAULT_PASSWORD', 'gv50')
    HEARTBEAT_INTERVAL: int = int(os.getenv('HEARTBEAT_INTERVAL', '30'))
    CONNECTION_TIMEOUT: int = int(os.getenv('CONNECTION_TIMEOUT', '3600'))  # 1 hour for long-connection
    MAX_CONNECTIONS: int = int(os.getenv('MAX_CONNECTIONS', '100'))
    
    # IP Change Configuration - para comando AT+GTIPSET
    NEW_DEVICE_IP: str = os.getenv('NEW_DEVICE_IP', '177.94.51.99')  # IP padrão para troca
    NEW_DEVICE_PORT: int = int(os.getenv('NEW_DEVICE_PORT', '8000'))  # Porta padrão para troca
    
    @classmethod
    def is_ip_allowed(cls, ip: str) -> bool:
        """Check if IP address is allowed to connect - apenas lista de IPs permitidos"""
        # Se não há IPs configurados, permite todos
        if not cls.ALLOWED_IPS:
            return True
        
        # Se contém 0.0.0.0/0, permite todos
        if '0.0.0.0/0' in cls.ALLOWED_IPS:
            return True
        
        # Se há IPs configurados, apenas esses são permitidos
        return ip in cls.ALLOWED_IPS
    
    @classmethod
    def reload_config(cls):
        """Reload configuration from environment variables"""
        load_dotenv(dotenv_path="../.env", override=True)
        # Reinitialize class attributes
        cls.__init_subclass__()