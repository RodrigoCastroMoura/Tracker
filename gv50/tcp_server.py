import asyncio
import time
from typing import Dict, List, Optional, Tuple
from config import Config
from logger import logger
from protocol_parser import protocol_parser
from database import db_manager


class AsyncGV50Server:
    """Asyncio TCP server for GV50 GPS tracker - replaces threaded version"""
    
    def __init__(self):
        self.server: Optional[asyncio.Server] = None
        self.running = False
        self.connected_clients: Dict[str, Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
        self.connected_devices: Dict[str, str] = {}
        self.commands_sent: Dict[str, float] = {}
        self.max_connections = Config.MAX_CONNECTIONS
        self.active_connections = 0
        self._server_task: Optional[asyncio.Task] = None
    
    async def start_server(self):
        """Start asyncio TCP server"""
        if not Config.SERVER_ENABLED:
            logger.info("Server is disabled in configuration")
            return
        
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                Config.SERVER_IP,
                Config.SERVER_PORT,
                backlog=self.max_connections
            )
            
            self.running = True
            logger.info(f"Asyncio GV50 TCP Server started on {Config.SERVER_IP}:{Config.SERVER_PORT}")
            print(f"Start server {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
            print(f"Houve um erro ao iniciar as {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle each client connection asynchronously"""
        addr = writer.get_extra_info('peername')
        client_ip = addr[0] if addr else "unknown"
        client_port = addr[1] if addr else 0
        connection_id = f"{client_ip}:{client_port}"
        
        if not Config.is_ip_allowed(client_ip):
            logger.warning(f"Connection rejected from blocked IP: {client_ip}")
            writer.close()
            await writer.wait_closed()
            return
        
        if self.active_connections >= self.max_connections:
            logger.warning(f"Max connections ({self.max_connections}) reached, rejecting {connection_id}")
            writer.close()
            await writer.wait_closed()
            return
        
        self.active_connections += 1
        self.connected_clients[connection_id] = (reader, writer)
        logger.info(f"New connection from {connection_id}")
        
        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(
                        reader.read(999999),
                        timeout=Config.CONNECTION_TIMEOUT
                    )
                    
                    if not data:
                        logger.info(f"Client {connection_id} disconnected (long-connection ended)")
                        break
                    
                    response = await self.read_callback(writer, data, client_ip)
                    
                    if response:
                        await self.send_data(writer, response)
                    
                    await self.send_heartbeat_if_needed(writer, client_ip)
                    
                except asyncio.TimeoutError:
                    logger.debug(f"Timeout on {connection_id}, sending heartbeat")
                    await self.send_heartbeat_if_needed(writer, client_ip)
                    continue
                except ConnectionResetError:
                    logger.warning(f"Connection reset for {connection_id}")
                    break
                except Exception as e:
                    logger.error(f"Error receiving data from {connection_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in handle_client for {connection_id}: {e}")
        finally:
            await self.cleanup_connection(writer, connection_id)
    
    async def read_callback(self, writer: asyncio.StreamWriter, data: bytes, client_ip: str) -> Optional[str]:
        """Process received data - TCP long-connection as recommended by manufacturer"""
        try:
            if len(data) < 1:
                return None
            
            try:
                message = data.decode('utf-8')
            except UnicodeDecodeError:
                message = data.decode('latin-1')
            
            addr = writer.get_extra_info('peername')
            connection_id = f"{client_ip}:{addr[1]}" if addr else client_ip
            
            response_parts = message.split(':')
            
            if len(response_parts) == 2:
                command_parts = response_parts[1].split(',')
                
                if len(command_parts) > 0:
                    msg_type = response_parts[0].strip()
                    
                    if msg_type == "+RESP":
                        await self.process_resp_message(command_parts, writer, client_ip)
                    elif msg_type == "+BUFF":
                        await self.process_buff_message(command_parts, writer, client_ip)
                    elif msg_type == "+ACK":
                        await self.process_ack_message(command_parts, writer, client_ip)
                    
                    logger.info(f"Keeping connection alive for {connection_id} (long-connection mode)")
            
            return None
                        
        except Exception as e:
            logger.error(f"Error in read_callback: {e}")
            return None
    
    async def process_resp_message(self, command_parts: List[str], writer: asyncio.StreamWriter, client_ip: str):
        """Process +RESP messages"""
        try:
            if len(command_parts) > 0:
                command_type = command_parts[0]
                
                if command_type == "GTFRI":
                    if len(command_parts) > 13:
                        imei = command_parts[2]
                        
                        first_connection = imei not in self.connected_devices
                        if first_connection:
                            self.connected_devices[imei] = client_ip
                        
                        await self.execute_immediate_commands(writer, imei)
                        
                        raw_message = '+RESP:' + ','.join(command_parts)
                        parsed_data = protocol_parser.parse_message(raw_message)
                        
                        if parsed_data and not parsed_data.get('error'):
                            vehicle_data = {
                                'imei': parsed_data.get('imei', imei),
                                'speed': parsed_data.get('speed', '0'),
                                'altitude': parsed_data.get('altitude', '0'),
                                'longitude': parsed_data.get('longitude', '0'),
                                'latitude': parsed_data.get('latitude', '0'),
                                'device_timestamp': parsed_data.get('device_timestamp', ''),
                                'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'raw_message': raw_message
                            }
                            logger.info(f"Parsed device timestamp: {parsed_data.get('device_timestamp', 'N/A')}")
                        else:
                            vehicle_data = {
                                'imei': imei,
                                'speed': command_parts[8],
                                'altitude': command_parts[10],
                                'longitude': command_parts[11],
                                'latitude': command_parts[12],
                                'device_timestamp': command_parts[13],
                                'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'raw_message': raw_message
                            }
                        
                        from message_handler import message_handler
                        response = await asyncio.to_thread(
                            message_handler.handle_incoming_message,
                            raw_message,
                            client_ip
                        )
                        
                        if response:
                            await self.send_data(writer, response)
                        
                        await self.send_command(writer, vehicle_data['imei'])
                        
                elif command_type in ["GTIGN", "GTIGF"]:
                    if len(command_parts) > 11:
                        imei = command_parts[2]
                        
                        first_connection = imei not in self.connected_devices
                        if first_connection:
                            self.connected_devices[imei] = client_ip
                        
                        await self.execute_immediate_commands(writer, imei)
                        
                        vehicle_data = {
                            'imei': imei,
                            'speed': command_parts[6],
                            'altitude': command_parts[8],
                            'longitude': command_parts[9],
                            'latitude': command_parts[10],
                            'device_timestamp': command_parts[19] if len(command_parts) > 19 else '',
                            'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'ignition': command_type == "GTIGN",
                            'raw_message': '+RESP:' + ','.join(command_parts)
                        }
                        
                        from message_handler import message_handler
                        await asyncio.to_thread(
                            message_handler.save_vehicle_data,
                            vehicle_data
                        )
                        
                        await asyncio.to_thread(
                            message_handler.update_vehicle_ignition,
                            vehicle_data['imei'],
                            vehicle_data['ignition']
                        )
                        
                        await self.send_command(writer, vehicle_data['imei'])
                        
        except Exception as e:
            logger.error(f"Error processing RESP message: {e}")
    
    async def process_buff_message(self, command_parts: List[str], writer: asyncio.StreamWriter, client_ip: str):
        """Process +BUFF messages"""
        try:
            if len(command_parts) > 0 and command_parts[0] == "GTFRI":
                if len(command_parts) > 13:
                    device_timestamp = command_parts[13]
                    if device_timestamp:
                        try:
                            year = device_timestamp[0:4]
                            month = device_timestamp[4:6] 
                            day = device_timestamp[6:8]
                            hour = device_timestamp[8:10]
                            minute = device_timestamp[10:12]
                            
                            device_time = f"{year}-{month}-{day} {hour}:{minute}"
                            current_time = time.strftime('%Y-%m-%d %H:%M')
                            
                            if device_time < current_time:
                                vehicle_data = {
                                    'imei': command_parts[2],
                                    'speed': command_parts[8],
                                    'altitude': command_parts[10],
                                    'longitude': command_parts[11],
                                    'latitude': command_parts[12],
                                    'device_timestamp': command_parts[13],
                                    'server_timestamp': device_time,
                                    'raw_message': '+BUFF:' + ','.join(command_parts)
                                }
                                
                                await self.execute_immediate_commands(writer, vehicle_data['imei'])
                                
                                from message_handler import message_handler
                                await asyncio.to_thread(
                                    message_handler.save_vehicle_data,
                                    vehicle_data
                                )
                                await self.send_command(writer, vehicle_data['imei'])
                        except Exception:
                            pass
                            
        except Exception as e:
            logger.error(f"Error processing BUFF message: {e}")
    
    async def process_ack_message(self, command_parts: List[str], writer: asyncio.StreamWriter, client_ip: str):
        """Process +ACK messages - filter GTHBD heartbeats"""
        try:
            if len(command_parts) > 0:
                command_type = command_parts[0]
                
                if command_type == "GTHBD":
                    if len(command_parts) > 2:
                        imei = command_parts[2]
                        logger.debug(f"Heartbeat received from IMEI {imei} at {client_ip}")
                        
                        if imei in self.connected_devices:
                            logger.debug(f"Heartbeat from known device {imei}")
                        else:
                            self.connected_devices[imei] = client_ip
                            logger.info(f"New device connected: IMEI {imei} from {client_ip}")
                        
                        logger.info(f"Checking pending commands for {imei} (heartbeat)")
                        await self.execute_immediate_commands(writer, imei)
                    return
                
                elif command_type == "GTOUT":
                    if len(command_parts) >= 3:
                        imei = command_parts[2]
                        status = command_parts[3] if len(command_parts) > 3 else "0000"
                        status = status.replace('$', '').strip()
                        
                        if status == "0000" or status == "":
                            vehicle = await asyncio.to_thread(db_manager.get_vehicle_by_imei, imei)
                            if vehicle:
                                if vehicle.get('comandobloqueo') == True:
                                    blocked = True
                                elif vehicle.get('comandobloqueo') == False:
                                    blocked = False
                                else:
                                    blocked = vehicle.get('bloqueado', False)
                                
                                from message_handler import message_handler
                                await asyncio.to_thread(
                                    message_handler.update_vehicle_blocking,
                                    imei,
                                    blocked
                                )
                                
                                keys_to_remove = [key for key in self.commands_sent.keys() if key.startswith(f"{imei}_")]
                                for key in keys_to_remove:
                                    del self.commands_sent[key]
                                logger.info(f"Cache cleared for {imei}")
                                
                                logger.info(f"Updated blocking status for {imei}: {'blocked' if blocked else 'unblocked'}")
                        else:
                            logger.info(f"Processing command ACK for {imei} with status: {status}")
                            vehicle = await asyncio.to_thread(db_manager.get_vehicle_by_imei, imei)
                            
                            if vehicle and vehicle.get('comandobloqueo') is not None:
                                if vehicle.get('comandobloqueo') == True:
                                    blocked = True
                                    logger.info(f"Blocking command confirmed for {imei} - Vehicle BLOCKED")
                                else:
                                    blocked = False
                                    logger.info(f"Unblocking command confirmed for {imei} - Vehicle UNBLOCKED")
                                
                                from message_handler import message_handler
                                await asyncio.to_thread(
                                    message_handler.update_vehicle_blocking,
                                    imei,
                                    blocked
                                )
                                
                                keys_to_remove = [key for key in self.commands_sent.keys() if key.startswith(f"{imei}_")]
                                for key in keys_to_remove:
                                    del self.commands_sent[key]
                                logger.info(f"Cache cleared for {imei}")
                                
                                logger.info(f"Updated blocking status for {imei}: {'BLOCKED' if blocked else 'UNBLOCKED'}")
                            else:
                                logger.warning(f"No pending command found for {imei} when processing ACK")
                    
        except Exception as e:
            logger.error(f"Error processing ACK message: {e}")
    
    async def send_command(self, writer: asyncio.StreamWriter, imei: str):
        """Send command to device if needed"""
        try:
            from message_handler import message_handler
            pending_command = message_handler.get_pending_command(imei)
            if pending_command:
                logger.warning(f"Sending command via TCP to {imei}: {pending_command}")
                await self.send_data(writer, pending_command)
        except Exception as e:
            logger.error(f"Error sending command: {e}")
    
    async def execute_immediate_commands(self, writer: asyncio.StreamWriter, imei: str):
        """Execute pending commands immediately"""
        try:
            vehicle = await asyncio.to_thread(db_manager.get_vehicle_by_imei, imei)
            
            if vehicle is None:
                return
            
            comando_pendente = vehicle.get('comandobloqueo')
            if comando_pendente is not None:
                command_key = f"{imei}_out"
                
                if command_key in self.commands_sent:
                    elapsed = time.time() - self.commands_sent[command_key]
                    if elapsed < 60:
                        logger.debug(f"Command already sent for {imei}, waiting for ACK ({elapsed:.0f}s ago)")
                        return
                
                if comando_pendente == True:
                    bit = "1"
                else:
                    bit = "0"
                
                comando = f"AT+GTOUT=gv50,{bit},,,,,,0,,,,,,,000{bit}$"
                
                logger.warning(f"Executing IMMEDIATE command for {imei}: {comando}")
                await self.send_data(writer, comando)
                
                self.commands_sent[command_key] = time.time()
                
        except Exception as e:
            logger.error(f"Error executing immediate commands for {imei}: {e}")
    
    async def send_data(self, writer: asyncio.StreamWriter, data: str):
        """Send data to client"""
        try:
            writer.write(data.encode('utf-8'))
            await writer.drain()
            logger.debug(f"Sent: {data}")
        except Exception as e:
            logger.error(f"Error sending data: {e}")
    
    async def send_heartbeat_if_needed(self, writer: asyncio.StreamWriter, client_ip: str):
        """Send heartbeat if connection is idle"""
        pass
    
    async def cleanup_connection(self, writer: asyncio.StreamWriter, connection_id: str):
        """Clean up connection resources"""
        try:
            if connection_id in self.connected_clients:
                del self.connected_clients[connection_id]
            
            for imei, ip in list(self.connected_devices.items()):
                if connection_id.startswith(ip):
                    del self.connected_devices[imei]
                    logger.info(f"Device {imei} disconnected")
                    break
            
            self.active_connections -= 1
            
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            
            logger.info(f"Connection {connection_id} cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up connection {connection_id}: {e}")
    
    def get_connection_count(self) -> int:
        """Get current connection count"""
        return self.active_connections
    
    def stop_server(self):
        """Stop the server"""
        self.running = False
        
        if self.server:
            self.server.close()
        
        logger.info("GV50 TCP Server stopped")


tcp_server = AsyncGV50Server()
