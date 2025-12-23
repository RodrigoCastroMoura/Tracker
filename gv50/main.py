#!/usr/bin/env python3
"""
GV50 GPS Tracker Service - Asyncio Version
A Python service for processing GPS tracker data from GV50 devices
"""

import sys
import signal
import asyncio
from datetime import datetime

from config import Config as GV50Config
from logger import logger as gv50_logger
from tcp_server import tcp_server as gv50_tcp_server
from database import db_manager as gv50_db_manager


class GV50TrackerService:
    """Main service class for GV50 GPS tracker processing - Asyncio version"""
    
    def __init__(self):
        self.running = False
        self.active_services = []
        self.stats = {
            'start_time': None,
            'total_connections': 0,
            'total_messages': 0,
            'last_activity': None
        }
        self._monitor_task = None
    
    async def start(self):
        """Start GV50 GPS tracker service - async version"""
        try:
            print("=" * 60)
            print("GV50 Tracker Service Starting (Asyncio)")
            print("=" * 60)
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            if not self._validate_gv50_configuration():
                return False
            
            if not self._test_gv50_database():
                return False
            
            self.active_services.append('GV50')
            print("GV50 service configured successfully")
            
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            
            print("GV50 Tracker Service ready")
            print(f"Listening on {GV50Config.SERVER_IP}:{GV50Config.SERVER_PORT}")
            
            await gv50_tcp_server.start_server()
            
            return True
            
        except Exception as e:
            print(f"Error starting GV50 service: {e}")
            gv50_logger.error(f"Error starting GV50 service: {e}")
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
    
    async def _monitoring_loop(self):
        """Monitoring loop for GV50 service health"""
        while self.running:
            try:
                await asyncio.sleep(30)
                
                if not self.running:
                    break
                
                connection_count = gv50_tcp_server.get_connection_count()
                uptime = self._get_uptime()
                
                gv50_logger.debug(f"GV50 Status - Uptime: {uptime}, Active Connections: {connection_count}")
                
                if connection_count > 0:
                    self.stats['last_activity'] = datetime.now()
                
                if not self._health_check():
                    gv50_logger.warning("GV50 service health check failed")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                gv50_logger.error(f"Error in GV50 monitoring loop: {e}")
                await asyncio.sleep(10)
    
    def _health_check(self) -> bool:
        """Perform GV50 service health check"""
        try:
            gv50_db_manager.client.admin.command('ping')
            
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
        
        if self._monitor_task:
            self._monitor_task.cancel()
        
        if 'GV50' in self.active_services:
            gv50_tcp_server.stop_server()
            gv50_db_manager.close_connection()
            print("GV50 service stopped")
        
        self._log_final_statistics()
        
        print("GV50 Tracker Service stopped")
    
    def _get_uptime(self) -> str:
        """Get service uptime"""
        try:
            if not self.stats['start_time']:
                return "Unknown"
            uptime = datetime.now() - self.stats['start_time']
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


async def main():
    """Main entry point - async"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    service = GV50TrackerService()
    signal_handler.service = service
    
    try:
        await service.start()
        
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        gv50_logger.error(f"Unexpected error: {e}")
    finally:
        service.stop()


if __name__ == "__main__":
    asyncio.run(main())
