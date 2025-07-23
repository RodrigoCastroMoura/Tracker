import os
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for GV50 tracker service"""
    
    # Service Configuration
    SERVER_ENABLED: bool = os.getenv('SERVER_ENABLED', 'true').lower() == 'true'
    SERVER_IP: str = os.getenv('SERVER_IP', '0.0.0.0')
    SERVER_PORT: int = int(os.getenv('SERVER_PORT', '8080'))
    
    # IP Management
    ALLOWED_IPS: List[str] = [ip.strip() for ip in os.getenv('ALLOWED_IPS', '').split(',') if ip.strip()]
    BLOCKED_IPS: List[str] = [ip.strip() for ip in os.getenv('BLOCKED_IPS', '').split(',') if ip.strip()]
    IP_WHITELIST_ENABLED: bool = os.getenv('IP_WHITELIST_ENABLED', 'false').lower() == 'true'
    
    # Logging Configuration
    LOGGING_ENABLED: bool = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_TO_FILE: bool = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
    LOG_TO_CONSOLE: bool = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
    LOG_ALL_MESSAGES: bool = os.getenv('LOG_ALL_MESSAGES', 'true').lower() == 'true'
    LOG_INCOMING_MESSAGES: bool = os.getenv('LOG_INCOMING_MESSAGES', 'true').lower() == 'true'
    LOG_OUTGOING_MESSAGES: bool = os.getenv('LOG_OUTGOING_MESSAGES', 'true').lower() == 'true'
    LOG_DATABASE_OPERATIONS: bool = os.getenv('LOG_DATABASE_OPERATIONS', 'false').lower() == 'true'
    SAVE_RAW_MESSAGES: bool = os.getenv('SAVE_RAW_MESSAGES', 'true').lower() == 'true'
    
    # Database Configuration
    MONGODB_URI: str = os.getenv('MONGODB_URI', 'mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/')
    DATABASE_NAME: str = os.getenv('DATABASE_NAME', 'gv50_tracker')
    
    # Protocol Configuration
    DEFAULT_PASSWORD: str = os.getenv('DEFAULT_PASSWORD', 'gv50')
    HEARTBEAT_INTERVAL: int = int(os.getenv('HEARTBEAT_INTERVAL', '30'))
    CONNECTION_TIMEOUT: int = int(os.getenv('CONNECTION_TIMEOUT', '300'))
    
    @classmethod
    def is_ip_allowed(cls, ip: str) -> bool:
        """Check if IP address is allowed to connect"""
        if ip in cls.BLOCKED_IPS:
            return False
        
        if cls.IP_WHITELIST_ENABLED:
            return ip in cls.ALLOWED_IPS
        
        return True
    
    @classmethod
    def reload_config(cls):
        """Reload configuration from environment variables"""
        load_dotenv(override=True)
        # Reinitialize class attributes
        cls.__init_subclass__()
