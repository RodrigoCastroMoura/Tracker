import logging
import os
from datetime import datetime
from typing import Optional
from config import Config

class GV50Logger:
    """Custom logger for GV50 tracker service"""
    
    def __init__(self):
        self.logger = logging.getLogger('GV50TrackerService')
        self.setup_logger()
    
    def setup_logger(self):
        """Setup logging configuration"""
        if not Config.LOGGING_ENABLED:
            self.logger.disabled = True
            return
        
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if Config.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if Config.LOG_TO_FILE:
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            file_handler = logging.FileHandler(
                f'logs/gv50_tracker_{datetime.now().strftime("%Y%m%d")}.log'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_incoming_message(self, client_ip: str, imei: str, raw_message: str):
        """Log incoming message from device"""
        if Config.LOG_INCOMING_MESSAGES and Config.LOG_ALL_MESSAGES:
            self.logger.info(f"INCOMING [{client_ip}] IMEI:{imei} - {raw_message}")
    
    def log_outgoing_message(self, client_ip: str, imei: str, response: str):
        """Log outgoing response to device"""
        if Config.LOG_OUTGOING_MESSAGES and Config.LOG_ALL_MESSAGES:
            self.logger.info(f"OUTGOING [{client_ip}] IMEI:{imei} - {response}")
    
    def log_database_operation(self, operation: str, collection: str, imei: str):
        """Log database operations"""
        if Config.LOG_DATABASE_OPERATIONS:
            self.logger.debug(f"DB_OP: {operation} on {collection} for IMEI:{imei}")
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

# Global logger instance
logger = GV50Logger()
