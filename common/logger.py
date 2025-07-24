import logging
import os
from datetime import datetime
from common.config import Config

class GV50Logger:
    """Simplified logger with only LOGGING_ENABLED option"""
    
    def __init__(self):
        self.logger = logging.getLogger('GV50TrackerService')
        self.setup_logger()
    
    def setup_logger(self):
        """Setup logger based on LOGGING_ENABLED only"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        if Config.LOGGING_ENABLED:
            # Enable logging with INFO level
            self.logger.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            file_handler = logging.FileHandler(
                f'logs/gv50_tracker_{datetime.now().strftime("%Y%m%d")}.log'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # Disable logging completely
            self.logger.setLevel(logging.CRITICAL + 1)
    
    def log_incoming_message(self, client_ip: str, imei: str, raw_message: str):
        """Log incoming message from device"""
        if Config.LOGGING_ENABLED:
            self.logger.info(f"INCOMING [{client_ip}] IMEI:{imei} - {raw_message}")
    
    def log_outgoing_message(self, client_ip: str, imei: str, response: str):
        """Log outgoing response to device"""
        if Config.LOGGING_ENABLED:
            self.logger.info(f"OUTGOING [{client_ip}] IMEI:{imei} - {response}")
    
    def log_database_operation(self, operation: str, collection: str, imei: str):
        """Log database operations"""
        if Config.LOGGING_ENABLED:
            self.logger.debug(f"DB_OP: {operation} on {collection} for IMEI:{imei}")
    
    def info(self, message: str):
        """Log info message"""
        if Config.LOGGING_ENABLED:
            self.logger.info(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        if Config.LOGGING_ENABLED:
            self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message: str):
        """Log warning message"""
        if Config.LOGGING_ENABLED:
            self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message"""
        if Config.LOGGING_ENABLED:
            self.logger.debug(message)

# Global logger instance
logger = GV50Logger()