#!/usr/bin/env python3
"""
GV50 Tracker Service
A Python service for processing GV50 GPS tracker data with MongoDB storage
"""

import sys
import signal
import time
import threading
from datetime import datetime

from common.config import Config
from common.logger import logger
from services.gv50.tcp_server import tcp_server
from common.database import db_manager

class GV50TrackerService:
    """Main service class for GV50 tracker processing"""
    
    def __init__(self):
        self.running = False
        self.server_thread = None
        self.stats = {
            'start_time': None,
            'total_connections': 0,
            'total_messages': 0,
            'last_activity': None
        }
    
    def start(self):
        """Start the GV50 tracker service"""
        try:
            logger.info("=" * 60)
            logger.info("GV50 Tracker Service Starting")
            logger.info("=" * 60)
            
            # Validate configuration
            if not self._validate_configuration():
                logger.error("Configuration validation failed")
                return False
            
            # Test database connection
            if not self._test_database_connection():
                logger.error("Database connection test failed")
                return False
            
            self.running = True
            self.stats['start_time'] = datetime.utcnow()
            
            # Start TCP server in separate thread
            self.server_thread = threading.Thread(
                target=tcp_server.start_server,
                daemon=True
            )
            self.server_thread.start()
            
            # Start monitoring thread
            monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            monitoring_thread.start()
            
            logger.info("GV50 Tracker Service started successfully")
            logger.info(f"Server listening on {Config.SERVER_IP}:{Config.SERVER_PORT}")
            logger.info(f"Database: {Config.DATABASE_NAME}")
            logger.info(f"Logging enabled: {Config.LOGGING_ENABLED}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting service: {e}", exc_info=True)
            return False
    
    def stop(self):
        """Stop the GV50 tracker service"""
        logger.info("Stopping GV50 Tracker Service...")
        
        self.running = False
        
        # Stop TCP server
        tcp_server.stop_server()
        
        # Wait for server thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=10)
        
        # Close database connection
        db_manager.close_connection()
        
        # Log service statistics
        self._log_final_statistics()
        
        logger.info("GV50 Tracker Service stopped")
    
    def _validate_configuration(self) -> bool:
        """Validate service configuration"""
        try:
            if not Config.SERVER_ENABLED:
                logger.warning("Server is disabled in configuration")
                return False
            
            if not Config.MONGODB_URI:
                logger.error("MongoDB URI not configured")
                return False
            
            if Config.SERVER_PORT < 1 or Config.SERVER_PORT > 65535:
                logger.error(f"Invalid server port: {Config.SERVER_PORT}")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return False
    
    def _test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            # Test connection by attempting to ping the database
            if db_manager.client:
                db_manager.client.admin.command('ping')
                logger.info("Database connection test passed")
                return True
            else:
                logger.error("Database client not initialized")
                return False
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def _monitoring_loop(self):
        """Monitoring loop for service health and statistics"""
        while self.running:
            try:
                time.sleep(30)  # Monitor every 30 seconds
                
                if not self.running:
                    break
                
                # Log service status
                connection_count = tcp_server.get_connection_count()
                uptime = self._get_uptime()
                
                logger.debug(f"Service Status - Uptime: {uptime}, Active Connections: {connection_count}")
                
                # Update statistics
                if connection_count > 0:
                    self.stats['last_activity'] = datetime.utcnow()
                
                # Health check
                if not self._health_check():
                    logger.warning("Service health check failed")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _health_check(self) -> bool:
        """Perform service health check"""
        try:
            # Check database connection
            db_manager.client.admin.command('ping')
            
            # Check if server is running
            if not tcp_server.running:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def _get_uptime(self) -> str:
        """Get service uptime"""
        try:
            if not self.stats['start_time']:
                return "Unknown"
            
            uptime = datetime.utcnow() - self.stats['start_time']
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
        except Exception:
            return "Unknown"
    
    def _log_final_statistics(self):
        """Log final service statistics"""
        try:
            uptime = self._get_uptime()
            
            logger.info("=" * 60)
            logger.info("GV50 Tracker Service Statistics")
            logger.info("=" * 60)
            logger.info(f"Total uptime: {uptime}")
            logger.info(f"Total connections: {self.stats['total_connections']}")
            logger.info(f"Total messages processed: {self.stats['total_messages']}")
            logger.info(f"Last activity: {self.stats['last_activity']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error logging final statistics: {e}")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    if 'service' in globals() and service:
        service.stop()
    sys.exit(0)

def main():
    """Main function"""
    global service
    
    try:
        # Initialize service
        service = GV50TrackerService()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start service
        if not service.start():
            logger.error("Failed to start service")
            sys.exit(1)
        
        # Keep service running
        try:
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'service' in locals():
            service.stop()

if __name__ == "__main__":
    main()
