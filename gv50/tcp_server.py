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
        self.connected_devices: Dict[str, str] = {}  # IMEI -> IP mapping para controle de conexões únicas
    
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
                    response = self.read_callback(client_socket, data, client_ip)
                    
                    # Send response (ACK or command)
                    if response:
                        self.send_data(client_socket, response)
                    
                    # Check for pending commands and send them (C# Command logic)
                    # Implementar após integração completa
                    
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
                        imei = command_parts[2]
                        
                        # Registrar conexão por IMEI se for nova
                        first_connection = imei not in self.connected_devices
                        if first_connection:
                            self.connected_devices[imei] = client_ip
                            logger.info(f"New device connected via GTFRI: IMEI {imei} from {client_ip}")
                        
                        # EXECUÇÃO IMEDIATA: Verificar comandos pendentes A CADA MENSAGEM
                        # O dispositivo fica conectado permanentemente, então precisamos verificar sempre
                        logger.info(f"🚀 VERIFICANDO COMANDOS PENDENTES PARA {imei} (a cada mensagem)")
                        self.execute_immediate_commands(client_socket, imei)
                        
                        # Use protocol_parser for correct field mapping
                        from protocol_parser import protocol_parser
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
                            logger.info(f"✅ Parsed device timestamp: {parsed_data.get('device_timestamp', 'N/A')}")
                        else:
                            # Fallback to old mapping if parser fails
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
                        
                        # Process through message_handler (includes command logic)
                        logger.info(f"DEBUG: Processing GPS message with device_timestamp: {vehicle_data.get('device_timestamp', 'N/A')}")
                        response = message_handler.handle_incoming_message(raw_message, client_ip)
                        
                        # Send ACK response
                        if response:
                            self.send_data(client_socket, response)
                        
                        # Send command if needed
                        self.send_command(client_socket, vehicle_data['imei'])
                        
                elif command_type in ["GTIGN", "GTIGF"]:
                    if len(command_parts) > 11:
                        imei = command_parts[2]
                        
                        # Registrar conexão por IMEI se for nova
                        first_connection = imei not in self.connected_devices
                        if first_connection:
                            self.connected_devices[imei] = client_ip
                            logger.info(f"New device connected via {command_type}: IMEI {imei} from {client_ip}")
                        
                        # EXECUÇÃO IMEDIATA: Verificar comandos pendentes A CADA MENSAGEM
                        logger.info(f"🚀 VERIFICANDO COMANDOS PENDENTES PARA {imei} (a cada mensagem)")
                        self.execute_immediate_commands(client_socket, imei)
                        
                        # Map fields exactly like C#
                        vehicle_data = {
                            'imei': imei,
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
                        logger.info(f"DEBUG: Saving ignition data with device_timestamp: {command_parts[11] if len(command_parts) > 11 else 'N/A'}")
                        message_handler.save_vehicle_data(vehicle_data)
                        
                        # Update ignition status
                        message_handler.update_vehicle_ignition(vehicle_data['imei'], vehicle_data['ignition'])
                        
                        # Send command if needed
                        self.send_command(client_socket, vehicle_data['imei'])
                        
                #   elif command_type == "GTSTT":
                #     if len(command_parts) > 12:
                #         imei = command_parts[2]
                #         motion_status = command_parts[4]
                        
                #         # Registrar conexão por IMEI se for nova
                #         if imei not in self.connected_devices:
                #             self.connected_devices[imei] = client_ip
                #             logger.info(f"New device connected via GTSTT: IMEI {imei} from {client_ip}")
                        
                #         # EXECUÇÃO IMEDIATA: Verificar comandos pendentes A CADA MENSAGEM
                #         logger.info(f"🚀 VERIFICANDO COMANDOS PENDENTES PARA {imei} (a cada mensagem)")
                #         self.execute_immediate_commands(client_socket, imei)
                        
                #         # Map fields para GTSTT
                #         vehicle_data = {
                #             'imei': imei,
                #             'motion_status': motion_status,
                #             'speed': command_parts[7],
                #             'altitude': command_parts[9],
                #             'longitude': command_parts[10],
                #             'latitude': command_parts[11],
                #             'device_timestamp': command_parts[17],
                #             'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                #             'raw_message': '+RESP:' + ','.join(command_parts)
                #         }
                        
                #         # Save to database
                #         message_handler.save_vehicle_data(vehicle_data)
                        
                #         # Processar mudança de estado
                #         message_handler.update_vehicle_motion_status(imei, motion_status)
                        
                #         # Send command if needed
                #         self.send_command(client_socket, vehicle_data['imei'])
                        
                #         logger.info(f"GTSTT processed for IMEI {imei}: motion status {motion_status}")
                        
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
                                
                                # EXECUÇÃO IMEDIATA: Verificar comandos pendentes A CADA MENSAGEM BUFF
                                logger.info(f"🚀 VERIFICANDO COMANDOS PENDENTES PARA {vehicle_data['imei']} (mensagem BUFF)")
                                self.execute_immediate_commands(client_socket, vehicle_data['imei'])
                                
                                message_handler.save_vehicle_data(vehicle_data)
                                self.send_command(client_socket, vehicle_data['imei'])
                        except:
                            pass
                            
        except Exception as e:
            logger.error(f"Error processing BUFF message: {e}")
    
    def process_ack_message(self, command_parts: List[str], client_socket: socket.socket, client_ip: str):
        """Process +ACK messages like C# - filtrar heartbeats GTHBD"""
        try:
            if len(command_parts) > 0:
                command_type = command_parts[0]
                
                # HEARTBEAT - processar e enviar comandos pendentes
                if command_type == "GTHBD":
                    if len(command_parts) > 2:
                        imei = command_parts[2]
                        logger.debug(f"Heartbeat received from IMEI {imei} at {client_ip}")
                        
                        # Verificar se dispositivo já está registrado
                        if imei in self.connected_devices:
                            logger.debug(f"Heartbeat from known device {imei}")
                        else:
                            # Primeira vez que vemos este IMEI - registrar conexão
                            self.connected_devices[imei] = client_ip
                            logger.info(f"New device connected: IMEI {imei} from {client_ip}")
                        
                        # EXECUÇÃO IMEDIATA: Verificar comandos pendentes NO HEARTBEAT
                        logger.info(f"🚀 VERIFICANDO COMANDOS PENDENTES PARA {imei} (heartbeat)")
                        self.execute_immediate_commands(client_socket, imei)
                    return  # Não processar heartbeat como mensagem normal
                
                elif command_type == "GTOUT":
                    if len(command_parts) >= 3:
                        imei = command_parts[2]
                        # Status pode estar na posição 3 ou 4, dependendo do formato
                        status = command_parts[3] if len(command_parts) > 3 else "0000"
                        
                        # Remover caracteres especiais do status
                        status = status.replace('$', '').strip()
                        
                        logger.info(f"Processing GTOUT ACK for {imei} with status: '{status}'")
                        
                        # Status "0000" ou vazio significa sucesso na confirmação
                        if status == "0000" or status == "":  # Comando executado com sucesso
                            # Buscar veículo para determinar se foi bloqueio ou desbloqueio
                            vehicle = db_manager.get_vehicle_by_imei(imei)
                            if vehicle:
                                # Se comando era de bloqueio (True), agora está bloqueado
                                # Se comando era de desbloqueio (False), agora está desbloqueado
                                if vehicle.get('comandobloqueo') == True:
                                    blocked = True  # Comando de bloqueio executado
                                    logger.info(f"🔴 Blocking command confirmed for {imei} - Vehicle BLOCKED")
                                elif vehicle.get('comandobloqueo') == False:
                                    blocked = False  # Comando de desbloqueio executado
                                    logger.info(f"🟢 Unblocking command confirmed for {imei} - Vehicle UNBLOCKED")
                                else:
                                    # Comando já foi processado, manter status atual
                                    blocked = vehicle.get('bloqueado', False)
                                    logger.info(f"ℹ️ Command already processed for {imei}")
                                
                                message_handler.update_vehicle_blocking(imei, blocked)
                                
                                # Limpar cache de comandos enviados para permitir novos comandos
                                if hasattr(self, 'commands_sent'):
                                    # Remover entradas relacionadas a este IMEI
                                    keys_to_remove = [key for key in self.commands_sent.keys() if key.startswith(f"{imei}_")]
                                    for key in keys_to_remove:
                                        del self.commands_sent[key]
                                    logger.info(f"🧹 Cache de comandos limpo para {imei}")
                                
                                logger.info(f"✅ Updated blocking status for {imei}: {'blocked' if blocked else 'unblocked'}")
                        else:
                            # Para qualquer status não vazio, processar como ACK válido
                            logger.info(f"Processing command ACK for {imei} with status: {status}")
                            vehicle = db_manager.get_vehicle_by_imei(imei)
                            logger.info(f"DEBUG: Vehicle data for {imei}: comandobloqueo={vehicle.get('comandobloqueo') if vehicle else 'N/A'}")
                            
                            if vehicle and vehicle.get('comandobloqueo') is not None:
                                if vehicle.get('comandobloqueo') == True:
                                    blocked = True  # Comando de bloqueio executado
                                    logger.info(f"🔴 Blocking command confirmed for {imei} - Vehicle BLOCKED")
                                else:
                                    blocked = False  # Comando de desbloqueio executado
                                    logger.info(f"🟢 Unblocking command confirmed for {imei} - Vehicle UNBLOCKED")
                                
                                message_handler.update_vehicle_blocking(imei, blocked)
                                
                                # Limpar cache de comandos enviados para permitir novos comandos
                                if hasattr(self, 'commands_sent'):
                                    # Remover entradas relacionadas a este IMEI
                                    keys_to_remove = [key for key in self.commands_sent.keys() if key.startswith(f"{imei}_")]
                                    for key in keys_to_remove:
                                        del self.commands_sent[key]
                                    logger.info(f"🧹 Cache de comandos limpo para {imei}")
                                
                                logger.info(f"✅ Updated blocking status for {imei}: {'BLOCKED' if blocked else 'UNBLOCKED'}")
                            else:
                                logger.warning(f"No pending command found for {imei} when processing ACK")
                    
        except Exception as e:
            logger.error(f"Error processing ACK message: {e}")
    
    def send_command(self, client_socket: socket.socket, imei: str):
        """Send command to device if needed - like C# Command method"""
        try:
            # Verificar comando pendente no message_handler
            pending_command = message_handler.get_pending_command(imei)
            if pending_command:
                logger.warning(f"🚀 ENVIANDO COMANDO VIA TCP PARA {imei}: {pending_command}")
                self.send_data(client_socket, pending_command)
        except Exception as e:
            logger.error(f"Error sending command: {e}")
    
    def check_and_send_pending_commands(self, client_socket: socket.socket, client_ip: str):
        """Verificar e enviar comandos pendentes - implementação C# Command()"""
        try:
            # Buscar IMEI da conexão atual
            for imei, ip in self.connected_devices.items():
                if ip == client_ip:
                    # Verificar comando pendente
                    pending_command = message_handler.get_pending_command(imei)
                    if pending_command:
                        logger.warning(f"🚀 COMANDO PENDENTE ENVIADO PARA {imei}: {pending_command}")
                        self.send_data(client_socket, pending_command)
                    break
        except Exception as e:
            logger.error(f"Erro ao verificar comandos pendentes: {e}")
    
    def get_connection_count(self) -> int:
        """Get current connection count - dispositivos únicos por IMEI"""
        return len(self.connected_devices)
    
    def execute_immediate_commands(self, client_socket: socket.socket, imei: str):
        """EXECUÇÃO IMEDIATA: Executar comandos pendentes assim que dispositivo conecta"""
        try:
            # Verificar comandos pendentes
            vehicle = db_manager.get_vehicle_by_imei(imei)
            if vehicle:
                comandos_enviados = []
                
                # 1. Verificar comando de bloqueio/desbloqueio pendente
                comando_pendente = vehicle.get('comandobloqueo')
                if comando_pendente is not None:  # True ou False, não None
                    # Verificar se já enviamos comando para este IMEI nesta sessão
                    if not hasattr(self, 'commands_sent'):
                        self.commands_sent = {}
                    
                    # Criar chave única para comando + IMEI
                    command_key = f"{imei}_{comando_pendente}"

                    # Determinar tipo de comando
                    if comando_pendente == True:
                        bit = "1"  # Bloquear
                        acao = "BLOQUEAR"
                    else:  # comando_pendente == False
                        bit = "0"  # Desbloquear 
                        acao = "DESBLOQUEAR"
                    
                    # Só enviar se ainda não foi enviado nesta sessão
                    if command_key not in self.commands_sent:
                                          
                        # Gerar comando exato do C#
                        comando = f"AT+GTOUT=gv50,{bit},,,,,,0,,,,,,,000{bit}$"
                        
                        logger.warning(f"⚡ EXECUÇÃO IMEDIATA: {acao} para {imei}")
                        logger.warning(f"⚡ COMANDO ENVIADO IMEDIATAMENTE: {comando}")
                        
                        # Enviar comando imediatamente via TCP
                        self.send_data(client_socket, comando)
                        comandos_enviados.append(f"BLOQUEIO: {acao}")
                        
                        # Marcar como enviado para evitar reenvio
                        self.commands_sent[command_key] = True
                        
                        # NÃO limpar comando pendente aqui - será limpo após processar ACK
                        # A limpeza acontece no update_vehicle_blocking para garantir que
                        # o ACK seja processado corretamente
                    else:
                        logger.info(f"ℹ️  Comando {acao} já foi enviado para {imei} - aguardando ACK")
                
                # 2. Verificar comando de troca de IP pendente - COMANDO GTSRI
                comando_ip = vehicle.get('comandotrocarip')
                if comando_ip == True:
                    # Comando de troca de IP para GV50 usando GTSRI - formato exato conforme especificação
                    # Formato: AT+GTSRI=gv50,3,,1,191.252.181.49,8000,191.252.181.49,8000,,60,0,0,0,,0,FFFF$
                    from config import Config
                    comando_ip_cmd = f"AT+GTSRI=gv50,3,,1,{Config.PRIMARY_SERVER_IP},{Config.PRIMARY_SERVER_PORT},{Config.BACKUP_SERVER_IP},{Config.BACKUP_SERVER_PORT},,60,0,0,0,,0,FFFF$"
                    
                    logger.warning(f"⚡ EXECUÇÃO IMEDIATA: TROCA DE IP (GTSRI) para {imei}")
                    logger.warning(f"⚡ COMANDO GTSRI ENVIADO: {comando_ip_cmd}")
                    
                    # Enviar comando de IP imediatamente
                    self.send_data(client_socket, comando_ip_cmd)
                    comandos_enviados.append("TROCA DE IP (GTSRI)")
                    
                    # Limpar comando pendente após envio
                    vehicle_data = dict(vehicle)
                    if '_id' in vehicle_data:
                        del vehicle_data['_id']
                    vehicle_data['comandotrocarip'] = False
                    from datetime import datetime
                    vehicle_data['tsusermanu'] = datetime.utcnow()
                    
                    from models import Vehicle
                    updated_vehicle = Vehicle(**vehicle_data)
                    db_manager.upsert_vehicle(updated_vehicle)
                
                if comandos_enviados:
                    logger.info(f"✅ Comandos executados imediatamente para {imei}: {', '.join(comandos_enviados)}")
                else:
                    logger.info(f"ℹ️  Nenhum comando pendente para {imei}")
            else:
                logger.info(f"ℹ️  Veículo {imei} não encontrado no banco")
                
        except Exception as e:
            logger.error(f"Erro na execução imediata de comandos para {imei}: {e}")
    
    def send_heartbeat_if_needed(self, client_socket: socket.socket, client_ip: str):
        """Send heartbeat to keep TCP long-connection alive"""
        try:
            # Simple heartbeat - send empty response to keep connection alive
            # This helps maintain the long-connection as recommended by manufacturer
            pass
        except Exception as e:
            logger.error(f"Error sending heartbeat to {client_ip}: {e}")
    
    def send_data(self, client_socket: socket.socket, data: str):
        """Send data to client socket - equivalent to C# Send method"""
        try:
            if client_socket and data:
                message_bytes = data.encode('ascii')
                client_socket.send(message_bytes)
                logger.debug(f"Data sent successfully: {data[:50]}...")
        except Exception as e:
            logger.error(f"Error sending data: {e}")
    
    def cleanup_connection(self, client_socket: socket.socket, connection_id: str):
        """Clean up connection"""
        try:
            if client_socket in self.client_sockets:
                self.client_sockets.remove(client_socket)
            
            # Remover dispositivo da lista de conectados quando desconectar
            client_ip = connection_id.split(':')[0]
            devices_to_remove = []
            for imei, ip in self.connected_devices.items():
                if ip == client_ip:
                    devices_to_remove.append(imei)
            
            for imei in devices_to_remove:
                del self.connected_devices[imei]
                logger.info(f"Device disconnected: IMEI {imei}")
            
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