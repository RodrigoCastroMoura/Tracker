import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../.env")

class Config:
    """Configuration class for GV50 tracker service - All variables from .env"""
    
    # Database Configuration
    MONGODB_URI: str = os.getenv('MONGODB_URI')
    DATABASE_NAME: str = os.getenv('DATABASE_NAME')
    
    # Server Configuration
    SERVER_IP: str = os.getenv('SERVER_IP')
    SERVER_PORT: int = int(os.getenv('SERVER_PORT'))
    SERVER_ENABLED: bool = os.getenv('SERVER_ENABLED', 'true').lower() == 'true'
    
    # Security Configuration
    ALLOWED_IPS: str = os.getenv('ALLOWED_IPS')
    BLOCKED_IPS: str = os.getenv('BLOCKED_IPS', '')
    
    # Protocol Configuration
    DEFAULT_PASSWORD: str = os.getenv('DEFAULT_PASSWORD')
    HEARTBEAT_INTERVAL: int = int(os.getenv('HEARTBEAT_INTERVAL'))
    CONNECTION_TIMEOUT: int = int(os.getenv('CONNECTION_TIMEOUT'))
    MAX_CONNECTIONS: int = int(os.getenv('MAX_CONNECTIONS'))
    
    # GTSRI Command Configuration
    PRIMARY_SERVER_IP: str = os.getenv('PRIMARY_SERVER_IP')
    PRIMARY_SERVER_PORT: int = int(os.getenv('PRIMARY_SERVER_PORT'))
    BACKUP_SERVER_IP: str = os.getenv('BACKUP_SERVER_IP')
    BACKUP_SERVER_PORT: int = int(os.getenv('BACKUP_SERVER_PORT'))
    
    # Logging Configuration - Minimal logs
    LOGGING_ENABLED: bool = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL')
    LOG_TO_FILE: bool = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
    LOG_INCOMING_MESSAGES: bool = os.getenv('LOG_INCOMING_MESSAGES', 'false').lower() == 'true'
    LOG_OUTGOING_MESSAGES: bool = os.getenv('LOG_OUTGOING_MESSAGES', 'false').lower() == 'true'
    
    @classmethod
    def is_ip_allowed(cls, ip: str) -> bool:
        """Check if IP address is allowed to connect"""
        if not cls.ALLOWED_IPS:
            return True
        if cls.ALLOWED_IPS == '0.0.0.0/0':
            return True
        return ip in cls.ALLOWED_IPS.split(',')