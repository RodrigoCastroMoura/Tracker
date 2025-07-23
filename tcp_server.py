import socket
import threading
import time
from typing import Dict, List
from config import Config
from logger import logger
from protocol_parser import protocol_parser
from message_handler import message_handler
from database import db_manager

class GV50TCPServer:
    """TCP server for handling GV50 device connections"""
    
    def __init__(self):
        self.server_socket = None
        self.running = False
        self.client_connections: Dict[str, socket.socket] = {}
        self.connection_threads: List[threading.Thread] = []
    
    def start_server(self):
        """Start the TCP server"""
        if not Config.SERVER_ENABLED:
            logger.info("Server is disabled in configuration")
            return
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((Config.SERVER_IP, Config.SERVER_PORT))
            self.server_socket.listen(100)  # Allow up to 100 concurrent connections
            
            self.running = True
            logger.info(f"GV50 TCP Server started on {Config.SERVER_IP}:{Config.SERVER_PORT}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_ip = client_address[0]
                    
                    # Check IP permissions
                    if not Config.is_ip_allowed(client_ip):
                        logger.warning(f"Connection rejected from blocked IP: {client_ip}")
                        client_socket.close()
                        continue
                    
                    logger.info(f"New connection from {client_ip}:{client_address[1]}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_ip),
                        daemon=True
                    )
                    client_thread.start()
                    self.connection_threads.append(client_thread)
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Error accepting connections: {e}")
                        time.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error starting server: {e}", exc_info=True)
        finally:
            self.stop_server()
    
    def handle_client(self, client_socket: socket.socket, client_ip: str):
        """Handle individual client connection"""
        connection_id = f"{client_ip}:{client_socket.getpeername()[1]}"
        self.client_connections[connection_id] = client_socket
        
        try:
            # Set socket timeout
            client_socket.settimeout(Config.CONNECTION_TIMEOUT)
            
            logger.info(f"Handling client connection: {connection_id}")
            
            while self.running:
                try:
                    # Receive data from client
                    data = client_socket.recv(4096)
                    
                    if not data:
                        logger.info(f"Client {connection_id} disconnected")
                        break
                    
                    # Decode message
                    try:
                        raw_message = data.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        raw_message = data.decode('latin-1').strip()
                    
                    if not raw_message:
                        continue
                    
                    logger.debug(f"Received from {connection_id}: {raw_message}")
                    
                    # Parse message
                    parsed_data = protocol_parser.parse_message(raw_message)
                    
                    if 'error' in parsed_data:
                        logger.warning(f"Parse error from {connection_id}: {parsed_data['error']}")
                        continue
                    
                    # Process message and get response
                    response = message_handler.process_message(parsed_data, client_ip)
                    
                    # Send acknowledgment if available
                    if response:
                        try:
                            client_socket.send(response.encode('utf-8'))
                            logger.debug(f"Sent to {connection_id}: {response}")
                        except socket.error as e:
                            logger.error(f"Error sending response to {connection_id}: {e}")
                            break
                    
                    # Check for pending commands
                    imei = parsed_data.get('imei')
                    if imei:
                        self.send_pending_commands(client_socket, imei, connection_id)
                    
                except socket.timeout:
                    logger.debug(f"Socket timeout for {connection_id}")
                    continue
                except socket.error as e:
                    logger.warning(f"Socket error for {connection_id}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error handling client {connection_id}: {e}", exc_info=True)
                    break
                    
        except Exception as e:
            logger.error(f"Unexpected error handling client {connection_id}: {e}", exc_info=True)
        finally:
            self.cleanup_client_connection(connection_id, client_socket)
    
    def send_pending_commands(self, client_socket: socket.socket, imei: str, connection_id: str):
        """Send pending commands to device"""
        try:
            pending_commands = db_manager.get_pending_commands(imei)
            
            for command_info in pending_commands:
                command = command_info.get('command')
                if command:
                    try:
                        client_socket.send(command.encode('utf-8'))
                        logger.info(f"Sent command to {connection_id} (IMEI: {imei}): {command}")
                        
                        # Log outgoing command
                        message_handler._log_outgoing_message(imei, connection_id.split(':')[0], command)
                        
                    except socket.error as e:
                        logger.error(f"Error sending command to {connection_id}: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"Error sending pending commands to {connection_id}: {e}")
    
    def cleanup_client_connection(self, connection_id: str, client_socket: socket.socket):
        """Clean up client connection"""
        try:
            if connection_id in self.client_connections:
                del self.client_connections[connection_id]
            
            client_socket.close()
            logger.info(f"Cleaned up connection: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up connection {connection_id}: {e}")
    
    def stop_server(self):
        """Stop the TCP server"""
        logger.info("Stopping GV50 TCP Server...")
        self.running = False
        
        # Close all client connections
        for connection_id, client_socket in self.client_connections.copy().items():
            try:
                client_socket.close()
                logger.debug(f"Closed client connection: {connection_id}")
            except Exception as e:
                logger.error(f"Error closing client connection {connection_id}: {e}")
        
        self.client_connections.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                logger.info("Server socket closed")
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")
        
        # Wait for threads to finish
        for thread in self.connection_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("GV50 TCP Server stopped")
    
    def get_connection_count(self) -> int:
        """Get current number of active connections"""
        return len(self.client_connections)
    
    def get_connection_info(self) -> Dict[str, str]:
        """Get information about active connections"""
        return {conn_id: "active" for conn_id in self.client_connections.keys()}

# Global server instance
tcp_server = GV50TCPServer()
