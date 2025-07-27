import logging
import os
from datetime import datetime
from config import Config

class GV50Logger:
    """Logger with categorical control via .env file"""
    
    def __init__(self):
        self.logger = logging.getLogger('GV50TrackerService')
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging with categorical control from .env"""
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set base log level
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._get_log_level())
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if enabled
        if Config.LOG_TO_FILE:
            log_dir = '../logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_filename = f"{log_dir}/gv50_tracker_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_filename, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _get_log_level(self):
        """Get log level from config"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        return level_map.get(Config.LOG_LEVEL, logging.INFO)
    
    def debug(self, message):
        """Debug level logging"""
        if Config.LOG_LEVEL == 'DEBUG':
            self.logger.debug(message)
    
    def info(self, message):
        """Info level logging"""
        if Config.LOG_LEVEL in ['DEBUG', 'INFO']:
            self.logger.info(message)
    
    def warning(self, message):
        """Warning level logging"""
        if Config.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING']:
            self.logger.warning(message)
    
    def error(self, message):
        """Error level logging"""
        self.logger.error(message)
    
    def log_incoming_message(self, ip, imei, message):
        """Log incoming protocol messages if enabled"""
        if Config.LOG_INCOMING_MESSAGES:
            self.info(f"← INCOMING [{ip}] IMEI:{imei} - {message[:100]}...")
    
    def log_outgoing_message(self, ip, imei, message):
        """Log outgoing protocol messages if enabled"""
        if Config.LOG_OUTGOING_MESSAGES:
            self.info(f"→ OUTGOING [{ip}] IMEI:{imei} - {message}")
    
    def log_protocol(self, message):
        """Log protocol-specific messages if protocol logging enabled"""
        if os.getenv('LOG_PROTOCOL', 'false').lower() == 'true':
            self.info(f"PROTOCOL: {message}")

# Global logger instance
logger = GV50Logger()