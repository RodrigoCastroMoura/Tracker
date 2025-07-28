import socket
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
from config import Config
from logger import logger
from message_handler import message_handler

class GV50TCPServer:
    """TCP Server for GV50 devices - Clean implementation without errors"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or Config.SERVER_IP
        self.port = port or Config.SERVER_PORT
        self.server_socket = None
        self.connected_devices: Dict[str, str] = {}  # IMEI -> IP mapping
        self.running = False
        
    def start(self):
        """Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(Config.MAX_CONNECTIONS)
            self.running = True
            
            logger.info(f"GV50 TCP Server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_ip = client_address[0]
                    
                    # Check IP access control
                    if not Config.is_ip_allowed(client_ip):
                        logger.warning(f"Connection rejected from blocked IP: {client_ip}")
                        client_socket.close()
                        continue
                    
                    logger.info(f"New connection from {client_ip}:{client_address[1]}")
                    
                    # Handle connection in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_ip)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
                        
        except Exception as e:
            logger.error(f"Error starting TCP server: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, client_ip: str):
        """Handle individual client connection"""
        connection_id = f"{client_ip}:{client_socket.getpeername()[1]}"
        logger.info(f"Handling client connection: {connection_id}")
        
        try:
            client_socket.settimeout(Config.CONNECTION_TIMEOUT)
            
            while self.running:
                try:
                    # Receive data from client
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    raw_message = data.decode('utf-8').strip()
                    if not raw_message:
                        continue
                    
                    logger.info(f"Message received {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(raw_message)
                    
                    # Process the message through message handler
                    response = message_handler.handle_incoming_message(raw_message, client_ip)
                    
                    # Send response if available
                    if response:
                        client_socket.send(response.encode('utf-8'))
                    
                    # Execute commands immediately after processing message
                    self._execute_immediate_commands(client_socket, raw_message)
                    
                    # Keep connection alive for long-connection mode
                    logger.info(f"Keeping connection alive for {connection_id} (long-connection mode)")
                    
                except socket.timeout:
                    logger.info(f"Connection timeout for {connection_id}")
                    break
                except ConnectionResetError:
                    logger.warning(f"Socket error for {connection_id}: Connection reset by peer")
                    break
                except Exception as e:
                    logger.error(f"Error in client handler for {connection_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client {connection_id}: {e}")
        finally:
            self._cleanup_connection(client_socket, connection_id)
    
    def _execute_immediate_commands(self, client_socket: socket.socket, raw_message: str):
        """Execute immediate commands based on incoming message"""
        try:
            # Extract IMEI from message for command execution
            imei = self._extract_imei_from_message(raw_message)
            if not imei:
                return
            
            # Get vehicle from database to check for pending commands
            from database import db_manager
            vehicle = db_manager.get_vehicle_by_imei(imei)
            if not vehicle:
                return
            
            commands_executed = []
            
            # Check for blocking/unblocking command (GTOUT)
            if vehicle.get('comandobloqueo') is not None:
                if vehicle.get('comandobloqueo'):
                    # Send blocking command
                    command = "AT+GTOUT=gv50,1,,,,,,0,,,,,,,0001$"
                    self._send_command(client_socket, command, imei, "BLOQUEIO")
                    commands_executed.append("BLOQUEIO (GTOUT)")
                else:
                    # Send unblocking command  
                    command = "AT+GTOUT=gv50,0,,,,,,0,,,,,,,0000$"
                    self._send_command(client_socket, command, imei, "DESBLOQUEIO")
                    commands_executed.append("DESBLOQUEIO (GTOUT)")
                
                # Clear command flag
                self._clear_command_flag(imei, 'comandobloqueo')
            
            # Check for IP change command (GTSRI)
            if vehicle.get('comandotrocarip'):
                command = f"AT+GTSRI=gv50,3,,1,{Config.PRIMARY_SERVER_IP},{Config.PRIMARY_SERVER_PORT},{Config.BACKUP_SERVER_IP},{Config.BACKUP_SERVER_PORT},,60,0,0,0,,0,FFFF$"
                self._send_command(client_socket, command, imei, "TROCA DE IP")
                commands_executed.append("TROCA DE IP (GTSRI)")
                
                # Clear command flag
                self._clear_command_flag(imei, 'comandotrocarip')
            
            if commands_executed:
                logger.info(f"Comandos executados para IMEI {imei}: {', '.join(commands_executed)}")
                
        except Exception as e:
            logger.error(f"Error executing immediate commands: {e}")
    
    def _extract_imei_from_message(self, raw_message: str) -> Optional[str]:
        """Extract IMEI from raw message"""
        try:
            # Remove protocol prefix and split by comma
            if raw_message.startswith(('+RESP:', '+BUFF:', '+ACK:')):
                parts = raw_message.split(',')
                if len(parts) > 2:
                    return parts[2]  # IMEI is typically in position 2
            return None
        except Exception:
            return None
    
    def _send_command(self, client_socket: socket.socket, command: str, imei: str, command_type: str):
        """Send command to device via socket"""
        try:
            client_socket.send(command.encode('utf-8'))
            logger.log_protocol(f"COMANDO {command_type} ENVIADO: {command}")
            logger.info(f"⚡ Comando {command_type} enviado para IMEI {imei}")
        except Exception as e:
            logger.error(f"Error sending {command_type} command to IMEI {imei}: {e}")
    
    def _clear_command_flag(self, imei: str, flag_name: str):
        """Clear command flag in database"""
        try:
            from database import db_manager
            vehicle = db_manager.get_vehicle_by_imei(imei)
            if vehicle:
                from models import Vehicle
                vehicle_data = dict(vehicle)
                if '_id' in vehicle_data:
                    del vehicle_data['_id']
                
                if flag_name == 'comandobloqueo':
                    vehicle_data['comandobloqueo'] = None
                elif flag_name == 'comandotrocarip':
                    vehicle_data['comandotrocarip'] = False
                
                vehicle_data['tsusermanu'] = datetime.utcnow()
                
                # Fix field name compatibility - Vehicle model expects IMEI (uppercase)
                if 'imei' in vehicle_data and 'IMEI' not in vehicle_data:
                    vehicle_data['IMEI'] = vehicle_data['imei']
                    del vehicle_data['imei']
                
                updated_vehicle = Vehicle(**vehicle_data)
                db_manager.upsert_vehicle(updated_vehicle)
                
        except Exception as e:
            logger.error(f"Error clearing {flag_name} flag for IMEI {imei}: {e}")
    
    def _cleanup_connection(self, client_socket: socket.socket, connection_id: str):
        """Clean up connection resources"""
        try:
            # Find and remove device from connected_devices
            imei_to_remove = None
            for imei, ip in self.connected_devices.items():
                if ip in connection_id:
                    imei_to_remove = imei
                    break
            
            if imei_to_remove:
                del self.connected_devices[imei_to_remove]
                logger.info(f"Device disconnected: IMEI {imei_to_remove}")
            
            client_socket.close()
            logger.info(f"Cleaned up connection: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up connection {connection_id}: {e}")
    
    def stop(self):
        """Stop the TCP server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
                logger.info("GV50 TCP Server stopped")
            except Exception as e:
                logger.error(f"Error stopping server: {e}")

# Global server instance
def start_server():
    """Start the GV50 TCP server"""
    server = GV50TCPServer()
    server.start()

if __name__ == "__main__":
    start_server()