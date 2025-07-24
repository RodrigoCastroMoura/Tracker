#!/usr/bin/env python3
"""
GPS Tracker Service
A Python service for processing GPS tracker data from multiple device types
"""

import sys
import signal
import time
import threading
from datetime import datetime

# Import GV50 service
from config import Config as GV50Config
from logger import logger as gv50_logger
from tcp_server_csharp_style import tcp_server as gv50_tcp_server
from database import db_manager as gv50_db_manager

class GV50TrackerService:
    """Main service class for GV50 GPS tracker processing"""
    
    def __init__(self):
        self.running = False
        self.service_threads = []
        self.active_services = []
        self.stats = {
            'start_time': None,
            'total_connections': 0,
            'total_messages': 0,
            'last_activity': None
        }
    
    def start(self):
        """Start GV50 GPS tracker service"""
        try:
            print("=" * 60)
            print("GV50 Tracker Service Starting")
            print("=" * 60)
            
            self.running = True
            self.stats['start_time'] = datetime.utcnow()
            
            # Start GV50 service
            if self._start_gv50_service():
                self.active_services.append('GV50')
                print("✓ GV50 service started successfully")
            
            print("GV50 Tracker Service ready")
            
            return len(self.active_services) > 0
            
        except Exception as e:
            print(f"Error starting GV50 service: {e}")
            return False
    
    def _start_gv50_service(self):
        """Start GV50 tracking service"""
        try:
            # Validate GV50 configuration
            if not self._validate_gv50_configuration():
                return False
            
            # Test GV50 database connection
            if not self._test_gv50_database():
                return False
            
            # Start GV50 TCP server in separate thread
            gv50_thread = threading.Thread(
                target=gv50_tcp_server.start_server,
                daemon=True,
                name="GV50-TCP-Server"
            )
            gv50_thread.start()
            self.service_threads.append(gv50_thread)
            
            # Start GV50 monitoring thread
            gv50_monitor_thread = threading.Thread(
                target=self._gv50_monitoring_loop,
                daemon=True,
                name="GV50-Monitor"
            )
            gv50_monitor_thread.start()
            self.service_threads.append(gv50_monitor_thread)
            
            return True
            
        except Exception as e:
            print(f"Error starting GV50 service: {e}")
            return False
    
    def _validate_gv50_configuration(self):
        """Validate GV50 service configuration"""
        try:
            gv50_logger.info("GV50 Configuration validation passed")
            return True
        except Exception as e:
            print(f"GV50 Configuration validation error: {e}")
            return False
    
    def _test_gv50_database(self):
        """Test GV50 database connectivity"""
        try:
            if gv50_db_manager.test_connection():
                gv50_logger.info("GV50 Database connection test passed")
                return True
            else:
                print("GV50 Database connection test failed")
                return False
        except Exception as e:
            print(f"GV50 Database connection test error: {e}")
            return False
    
    def _gv50_monitoring_loop(self):
        """Monitoring loop for GV50 service health"""
        while self.running:
            try:
                time.sleep(30)  # Monitor every 30 seconds
                
                if not self.running:
                    break
                
                # Log GV50 service status
                connection_count = gv50_tcp_server.get_connection_count()
                uptime = self._get_uptime()
                
                gv50_logger.debug(f"GV50 Status - Uptime: {uptime}, Active Connections: {connection_count}")
                
                # Update statistics
                if connection_count > 0:
                    self.stats['last_activity'] = datetime.utcnow()
                
                # Health check
                if not self._gv50_health_check():
                    gv50_logger.warning("GV50 service health check failed")
                
            except Exception as e:
                gv50_logger.error(f"Error in GV50 monitoring loop: {e}")
                time.sleep(10)
    
    def _gv50_health_check(self) -> bool:
        """Perform GV50 service health check"""
        try:
            # Check database connection
            gv50_db_manager.client.admin.command('ping')
            
            # Check if server is running
            if not gv50_tcp_server.running:
                return False
            
            return True
            
        except Exception as e:
            gv50_logger.error(f"GV50 health check failed: {e}")
            return False
    
    def stop(self):
        """Stop GV50 GPS tracker service"""
        print("Stopping GV50 Tracker Service...")
        
        self.running = False
        
        # Stop GV50 service
        if 'GV50' in self.active_services:
            gv50_tcp_server.stop_server()
            gv50_db_manager.close_connection()
            print("✓ GV50 service stopped")
        
        # Wait for service threads to finish
        for thread in self.service_threads:
            if thread.is_alive():
                thread.join(timeout=10)
        
        # Log service statistics
        self._log_final_statistics()
        
        print("GV50 Tracker Service stopped")
    
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
            print(f"Service Statistics - Uptime: {uptime}")
            print(f"Active Services: {', '.join(self.active_services) if self.active_services else 'None'}")
            
        except Exception as e:
            print(f"Error logging statistics: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}, shutting down...")
    if hasattr(signal_handler, 'service'):
        signal_handler.service.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start service
    service = GV50TrackerService()
    signal_handler.service = service  # Store reference for signal handler
    
    try:
        if service.start():
            # Keep the main thread alive
            while service.running:
                time.sleep(1)
        else:
            print("Failed to start GV50 Tracker Service")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        service.stop()

if __name__ == "__main__":
    main()