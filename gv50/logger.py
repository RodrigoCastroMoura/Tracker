import logging
import os
from datetime import datetime
from config import Config

def setup_logger():
    """Setup logger with minimal configuration for clean logs"""
    logger = logging.getLogger('GV50TrackerService')
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set log level to ERROR only for clean operation
    logger.setLevel(logging.ERROR)
    
    # Only add console handler with minimal format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    
    # Simple formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger

# Global logger instance
logger = setup_logger()