import os
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for GV50 tracker service"""
    
    # Service Configuration - fixos
    SERVER_ENABLED: bool = True
    SERVER_IP: str = '0.0.0.0'
    SERVER_PORT: int = int(os.getenv('SERVER_PORT', '5000'))
    
    # IP Management - apenas IPs permitidos (configurável)
    ALLOWED_IPS: List[str] = [ip.strip() for ip in os.getenv('ALLOWED_IPS', '').split(',') if ip.strip()]
    
    # Logging Configuration - apenas ativar/desativar log
    LOGGING_ENABLED: bool = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'
    
    # Database Configuration - fixos
    MONGODB_URI: str = os.getenv('MONGODB_URI', 'mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/')
    DATABASE_NAME: str = os.getenv('DATABASE_NAME', 'gv50_tracker')
    
    # Protocol Configuration - fixos
    DEFAULT_PASSWORD: str = 'gv50'
    HEARTBEAT_INTERVAL: int = 30
    CONNECTION_TIMEOUT: int = 300
    
    @classmethod
    def is_ip_allowed(cls, ip: str) -> bool:
        """Check if IP address is allowed to connect - apenas lista de IPs permitidos"""
        # Se não há IPs configurados, permite todos
        if not cls.ALLOWED_IPS:
            return True
        
        # Se há IPs configurados, apenas esses são permitidos
        return ip in cls.ALLOWED_IPS
    
    @classmethod
    def reload_config(cls):
        """Reload configuration from environment variables"""
        load_dotenv(override=True)
        # Reinitialize class attributes
        cls.__init_subclass__()
