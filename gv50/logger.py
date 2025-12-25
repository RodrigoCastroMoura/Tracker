import logging
import os
from datetime import datetime
from config import Config

class GV50Logger:
    """Logger with configurable console and file output"""
    
    def __init__(self):
        self.logger = logging.getLogger('GV50TrackerService')
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration based on environment variables"""
        # Read config from environment
        logging_enabled = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'
        console_logs = os.getenv('ENABLE_CONSOLE_LOGS', 'true').lower() == 'true'
        file_logs = os.getenv('ENABLE_FILE_LOGS', 'true').lower() == 'true'
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # If logging completely disabled, disable logger
        if not logging_enabled:
            self.logger.disabled = True
            return
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(log_level, logging.INFO))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (if enabled)
        if console_logs:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level_map.get(log_level, logging.INFO))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if file_logs:
            log_dir = '../logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Separate files by log level for better organization
            if log_level == 'DEBUG':
                log_filename = f"{log_dir}/gv50_tracker_debug_{datetime.now().strftime('%Y%m%d')}.log"
            else:
                log_filename = f"{log_dir}/gv50_tracker_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_filename, encoding='utf-8')
            file_handler.setLevel(level_map.get(log_level, logging.INFO))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        # Log initialization
        if console_logs or file_logs:
            self.logger.info(f"Logging initialized - Level: {log_level}, Console: {console_logs}, File: {file_logs}")
    
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
    
    def critical(self, message):
        """Critical level logging"""
        self.logger.critical(message)
    
    def log_database_operation(self, operation: str, table: str, imei: str):
        """Log database operations - only at DEBUG level"""
        self.logger.debug(f"DB: {operation} on {table} for IMEI {imei}")
    
    def log_outgoing_message(self, client_ip: str, imei: str, message: str):
        """Log outgoing messages - only at DEBUG level"""
        self.logger.debug(f"OUT -> {client_ip} (IMEI: {imei}): {message[:100]}")

# Global logger instance
logger = GV50Logger()