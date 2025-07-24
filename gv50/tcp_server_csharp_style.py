import socket
import threading
import time
from typing import Dict, List
from config import Config
from logger import logger
from protocol_parser import protocol_parser
from message_handler import message_handler
from database import db_manager

class GV50TCPServerCSharpStyle:
    """TCP server implementing C# style connection handling"""
    
    def __init__(self):
        self.server_socket = None
        self.running = False
        self.client_sockets: List[socket.socket] = []
        self.listener_thread = None
        self.bytes_buffer = bytearray(999999999)  # Large buffer like C#
    
    def start_server(self):
        """Start the TCP server - C# style"""
        if not Config.SERVER_ENABLED:
            logger.info("Server is disabled in configuration")
            return
        
        try:
            # Create socket exactly like C#
            if self.server_socket is None:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((Config.SERVER_IP, Config.SERVER_PORT))
            self.server_socket.listen(999)  # Large listen queue like C#
            
            self.running = True
            logger.info(f"GV50 TCP Server started on {Config.SERVER_IP}:{Config.SERVER_PORT}")
            print(f"Start server {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Start accepting connections in continuous loop like C#
            self.start_listening()
            
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
            print(f"Houve um erro ao iniciar as {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def start_listening(self):
        """Main listening loop - equivalent to C# StartListening()"""
        while self.running:
            try:
                # Accept connection
                client_socket, client_address = self.server_socket.accept()
                client_ip = client_address[0]
                
                # Check IP permissions
                if not Config.is_ip_allowed(client_ip):
                    logger.warning(f"Connection rejected from blocked IP: {client_ip}")
                    client_socket.close()
                    continue
                
                logger.info(f"New connection from {client_ip}:{client_address[1]}")
                
                # Add to client list
                self.client_sockets.append(client_socket)
                
                # Start receiving data from this client - equivalent to C# BeginReceive
                receive_thread = threading.Thread(
                    target=self.begin_receive, 
                    args=(client_socket, client_ip),
                    daemon=True
                )
                receive_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
                break
    
    def begin_receive(self, client_socket: socket.socket, client_ip: str):
        """Begin receiving data - equivalent to C# BeginReceive"""
        connection_id = f"{client_ip}:{client_socket.getpeername()[1]}"
        
        try:
            # Set timeout
            client_socket.settimeout(Config.CONNECTION_TIMEOUT)
            
            logger.info(f"Handling client connection: {connection_id}")
            
            while self.running and client_socket.fileno() != -1:
                try:
                    # Receive data with large buffer like C#
                    data = client_socket.recv(len(self.bytes_buffer))
                    
                    if not data:
                        logger.info(f"Client {connection_id} disconnected (long-connection ended)")
                        break
                    
                    # Process received data - equivalent to C# ReadCallback
                    self.read_callback(client_socket, data, client_ip)
                    
                    # Send heartbeat/keep-alive if needed
                    self.send_heartbeat_if_needed(client_socket, client_ip)
                    
                except socket.timeout:
                    # Send heartbeat on timeout to keep connection alive
                    logger.debug(f"Timeout on {connection_id}, sending heartbeat")
                    self.send_heartbeat_if_needed(client_socket, client_ip)
                    continue
                except socket.error as e:
                    logger.warning(f"Socket error for {connection_id}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error receiving data from {connection_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in begin_receive for {connection_id}: {e}")
        finally:
            self.cleanup_connection(client_socket, connection_id)
    
    def read_callback(self, client_socket: socket.socket, data: bytes, client_ip: str):
        """Process received data - TCP long-connection as recommended by manufacturer"""
        try:
            if len(data) < 1:
                return
            
            # Decode message exactly like C#
            try:
                message = data.decode('utf-8')
            except UnicodeDecodeError:
                message = data.decode('latin-1')
            
            connection_id = f"{client_ip}:{client_socket.getpeername()[1]}"
            
            # Log the message like C#
            print(f"\nMessage received {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(message)
            logger.debug(f"Received from {connection_id}: {message}")
            
            # Parse message like C# does with split
            response_parts = message.split(':')
            
            if len(response_parts) == 2:
                command_parts = response_parts[1].split(',')
                
                if len(command_parts) > 0:
                    msg_type = response_parts[0].strip()
                    command_type = command_parts[0]
                    
                    # Process based on message type like C#
                    if msg_type == "+RESP":
                        self.process_resp_message(command_parts, client_socket, client_ip)
                    elif msg_type == "+BUFF":
                        self.process_buff_message(command_parts, client_socket, client_ip)
                    elif msg_type == "+ACK":
                        self.process_ack_message(command_parts, client_socket, client_ip)
                    
                    # KEEP CONNECTION ALIVE - TCP long-connection as recommended
                    logger.info(f"Keeping connection alive for {connection_id} (long-connection mode)")
                        
        except Exception as e:
            logger.error(f"Error in read_callback: {e}")
    
    def process_resp_message(self, command_parts: List[str], client_socket: socket.socket, client_ip: str):
        """Process +RESP messages like C#"""
        try:
            if len(command_parts) > 0:
                command_type = command_parts[0]
                
                if command_type == "GTFRI":
                    if len(command_parts) > 13:
                        # Map fields exactly like C#
                        vehicle_data = {
                            'imei': command_parts[2],
                            'speed': command_parts[8],
                            'altitude': command_parts[10],
                            'longitude': command_parts[11],
                            'latitude': command_parts[12],
                            'device_timestamp': command_parts[13],
                            'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'raw_message': '+RESP:' + ','.join(command_parts)
                        }
                        
                        # Save to database
                        message_handler.save_vehicle_data(vehicle_data)
                        
                        # Send command if needed
                        self.send_command(client_socket, vehicle_data['imei'])
                        
                elif command_type in ["GTIGN", "GTIGF"]:
                    if len(command_parts) > 11:
                        # Map fields exactly like C#
                        vehicle_data = {
                            'imei': command_parts[2],
                            'speed': command_parts[6],
                            'altitude': command_parts[8],
                            'longitude': command_parts[9],
                            'latitude': command_parts[10],
                            'device_timestamp': command_parts[11],
                            'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'ignition': command_type == "GTIGN",
                            'raw_message': '+RESP:' + ','.join(command_parts)
                        }
                        
                        # Save to database
                        message_handler.save_vehicle_data(vehicle_data)
                        
                        # Update ignition status
                        message_handler.update_vehicle_ignition(vehicle_data['imei'], vehicle_data['ignition'])
                        
                        # Send command if needed
                        self.send_command(client_socket, vehicle_data['imei'])
                        
        except Exception as e:
            logger.error(f"Error processing RESP message: {e}")
    
    def process_buff_message(self, command_parts: List[str], client_socket: socket.socket, client_ip: str):
        """Process +BUFF messages like C#"""
        try:
            if len(command_parts) > 0 and command_parts[0] == "GTFRI":
                if len(command_parts) > 13:
                    # Same as RESP but check timestamp
                    device_timestamp = command_parts[13]
                    if device_timestamp:
                        # Parse timestamp like C#
                        try:
                            year = device_timestamp[0:4]
                            month = device_timestamp[4:6] 
                            day = device_timestamp[6:8]
                            hour = device_timestamp[8:10]
                            minute = device_timestamp[10:12]
                            
                            device_time = f"{year}-{month}-{day} {hour}:{minute}"
                            current_time = time.strftime('%Y-%m-%d %H:%M')
                            
                            # Only save if device time is before current time
                            if device_time < current_time:
                                vehicle_data = {
                                    'imei': command_parts[2],
                                    'speed': command_parts[8],
                                    'altitude': command_parts[10],
                                    'longitude': command_parts[11],
                                    'latitude': command_parts[12],
                                    'device_timestamp': command_parts[13],
                                    'server_timestamp': device_time,  # Use device time
                                    'raw_message': '+BUFF:' + ','.join(command_parts)
                                }
                                
                                message_handler.save_vehicle_data(vehicle_data)
                                self.send_command(client_socket, vehicle_data['imei'])
                        except:
                            pass
                            
        except Exception as e:
            logger.error(f"Error processing BUFF message: {e}")
    
    def process_ack_message(self, command_parts: List[str], client_socket: socket.socket, client_ip: str):
        """Process +ACK messages like C#"""
        try:
            if len(command_parts) > 0 and command_parts[0] == "GTOUT":
                if len(command_parts) > 4:
                    imei = command_parts[2]
                    status = command_parts[4]
                    
                    # Update vehicle blocking status like C#
                    blocked = (status == "0000")
                    message_handler.update_vehicle_blocking(imei, blocked)
                    
                    logger.info(f"Vehicle {imei} {'blocked' if blocked else 'unblocked'}")
                    
        except Exception as e:
            logger.error(f"Error processing ACK message: {e}")
    
    def send_command(self, client_socket: socket.socket, imei: str):
        """Send command to device if needed - like C# Command method"""
        try:
            # Simple command check - no database commands for now
            logger.debug(f"Checking commands for {imei}")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
    
    def get_connection_count(self) -> int:
        """Get current connection count"""
        return len(self.client_sockets)
    
    def send_heartbeat_if_needed(self, client_socket: socket.socket, client_ip: str):
        """Send heartbeat to keep TCP long-connection alive"""
        try:
            # Simple heartbeat - send empty response to keep connection alive
            # This helps maintain the long-connection as recommended by manufacturer
            pass
        except Exception as e:
            logger.error(f"Error sending heartbeat to {client_ip}: {e}")
    
    def cleanup_connection(self, client_socket: socket.socket, connection_id: str):
        """Clean up connection"""
        try:
            if client_socket in self.client_sockets:
                self.client_sockets.remove(client_socket)
            client_socket.close()
            logger.info(f"Cleaned up connection: {connection_id}")
        except:
            pass
    
    def stop_server(self):
        """Stop the server"""
        self.running = False
        
        # Close all client connections
        for client_socket in self.client_sockets[:]:
            try:
                client_socket.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("GV50 TCP Server stopped")

# Create server instance
tcp_server = GV50TCPServerCSharpStyle()