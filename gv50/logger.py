import logging
import os
from datetime import datetime
from config import Config

class GV50Logger:
    """Simplified logger with only LOGGING_ENABLED option"""
    
    def __init__(self):
        self.logger = logging.getLogger('GV50TrackerService')
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration - sempre ativo"""
        # Verificar se logs estão desabilitados via variável de ambiente
        logging_enabled = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'
        if not logging_enabled:
            self.logger.disabled = True
            return
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set log level to ERROR only for performance
        self.logger.setLevel(logging.ERROR)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler - only errors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler - apenas erros para melhor desempenho
        log_dir = '../logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_filename = f"{log_dir}/gv50_tracker_errors_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message):
        """Debug level logging"""
        self.logger.debug(message)
    
    def info(self, message):
        """Info level logging"""
        self.logger.info(message)
    
    def warning(self, message):
        """Warning level logging"""
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        """Error level logging"""
        self.logger.error(message, exc_info=exc_info)
    
    def log_database_operation(self, operation: str, table: str, imei: str):
        """Log database operations - disabled for performance"""
        pass
    
    def log_outgoing_message(self, client_ip: str, imei: str, message: str):
        """Log outgoing messages - disabled for performance"""
        pass

# Global logger instance
logger = GV50Logger()