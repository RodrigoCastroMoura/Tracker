from datetime import datetime
from typing import Dict, Optional, Any
from database import db_manager
from protocol_parser import protocol_parser
from logger import logger
from models import VehicleData, Vehicle
from datetime_converter import convert_device_timestamp

class MessageHandler:
    """Handle parsed messages and update database - duas tabelas apenas"""
    
    def __init__(self):
        self.device_ips = {}  # Track IP addresses for IP change detection
    
    def handle_incoming_message(self, raw_message: str, client_ip: str) -> Optional[str]:
        """Handle incoming GPS device message - simplified for 2 tables only"""
        try:
            # Log incoming message if enabled
            logger.log_incoming_message(client_ip, "parsing...", raw_message)
            
            # Parse the raw message
            parsed_data = protocol_parser.parse_message(raw_message)
            
            if not parsed_data:
                logger.warning(f"Unable to parse message from {client_ip}: {raw_message[:100]}...")
                return None
            
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning(f"No IMEI found in message from {client_ip}")
                return None
            
            # Log IP change detection
            if imei in self.device_ips and self.device_ips[imei] != client_ip:
                logger.info(f"IP change detected for IMEI {imei}: {self.device_ips[imei]} -> {client_ip}")
            self.device_ips[imei] = client_ip
            
            # Save vehicle data to vehicle_data table
            self.save_vehicle_data(parsed_data, raw_message)
            
            # Update vehicle information in vehicles table
            self.update_vehicle(parsed_data, client_ip, raw_message)
            
            # Generate acknowledgment
            response = protocol_parser.generate_acknowledgment(parsed_data)
            if response:
                logger.log_outgoing_message(client_ip, imei, response)
            
            # Execute command logic (GTOUT and GTSRI)
            self._execute_command_logic(imei, client_ip)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message from {client_ip}: {e}")
            return None
    
    def save_vehicle_data(self, parsed_data: Dict[str, Any], raw_message: str):
        """Save GPS data to vehicle_data table"""
        try:
            imei = parsed_data.get('imei', '')
            current_time = datetime.utcnow()
            
            # Convert device timestamp to datetime
            device_timestamp_str = parsed_data.get('device_timestamp', '')
            device_datetime_converted = None
            if device_timestamp_str and device_timestamp_str != '0000':
                device_datetime_converted = convert_device_timestamp(device_timestamp_str)
            
            # Create vehicle data record
            vehicle_data = VehicleData(
                imei=imei,
                longitude=parsed_data.get('longitude'),
                latitude=parsed_data.get('latitude'),
                altitude=parsed_data.get('altitude'),
                timestamp=current_time,  # Server timestamp
                deviceTimestamp=device_datetime_converted,  # Device timestamp converted to datetime
                systemDate=current_time,  # System timestamp
                mensagem_raw=raw_message
            )
            
            # Save to database
            db_manager.insert_vehicle_data(vehicle_data)
            logger.debug(f"Vehicle data saved for IMEI: {imei}")
            
        except Exception as e:
            logger.error(f"Error saving vehicle data: {e}")
    
    def update_vehicle(self, parsed_data: Dict[str, Any], client_ip: str, raw_message: str):
        """Update vehicle information in vehicles table"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                return
                
            report_type = parsed_data.get('report_type', '')
            
            # Get existing vehicle or create basic structure
            vehicle = db_manager.get_vehicle_by_imei(imei)
            
            # Update ignition status based on message type
            if report_type == 'GTIGN':  # Ignition ON
                if vehicle:
                    vehicle_data = dict(vehicle)
                    if '_id' in vehicle_data:
                        del vehicle_data['_id']
                    vehicle_data['ignicao'] = True
                    vehicle_data['tsusermanu'] = datetime.utcnow()
                    updated_vehicle = Vehicle(**vehicle_data)
                    db_manager.upsert_vehicle(updated_vehicle)
                    logger.debug(f"Ignition ON updated for IMEI: {imei}")
                    
            elif report_type == 'GTIGF':  # Ignition OFF
                if vehicle:
                    vehicle_data = dict(vehicle)
                    if '_id' in vehicle_data:
                        del vehicle_data['_id']
                    vehicle_data['ignicao'] = False
                    vehicle_data['tsusermanu'] = datetime.utcnow()
                    updated_vehicle = Vehicle(**vehicle_data)
                    db_manager.upsert_vehicle(updated_vehicle)
                    logger.debug(f"Ignition OFF updated for IMEI: {imei}")
                    
        except Exception as e:
            logger.error(f"Error updating vehicle: {e}")
    
    def _execute_command_logic(self, imei: str, client_socket):
        """Execute command logic from C# - GTOUT and GTSRI"""
        try:
            # Get vehicle from database
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
                from config import Config
                command = f"AT+GTSRI=gv50,3,,1,{Config.PRIMARY_SERVER_IP},{Config.PRIMARY_SERVER_PORT},{Config.BACKUP_SERVER_IP},{Config.BACKUP_SERVER_PORT},,60,0,0,0,,0,FFFF$"
                self._send_command(client_socket, command, imei, "TROCA DE IP")
                commands_executed.append("TROCA DE IP (GTSRI)")
                
                # Clear command flag
                self._clear_command_flag(imei, 'comandotrocarip')
            
            if commands_executed:
                logger.info(f"Comandos executados para IMEI {imei}: {', '.join(commands_executed)}")
                
        except Exception as e:
            logger.error(f"Error executing commands for IMEI {imei}: {e}")
    
    def _send_command(self, client_socket, command: str, imei: str, command_type: str):
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
            vehicle = db_manager.get_vehicle_by_imei(imei)
            if vehicle:
                vehicle_data = dict(vehicle)
                if '_id' in vehicle_data:
                    del vehicle_data['_id']
                
                if flag_name == 'comandobloqueo':
                    vehicle_data['comandobloqueo'] = None
                elif flag_name == 'comandotrocarip':
                    vehicle_data['comandotrocarip'] = False
                
                vehicle_data['tsusermanu'] = datetime.utcnow()
                updated_vehicle = Vehicle(**vehicle_data)
                db_manager.upsert_vehicle(updated_vehicle)
                
        except Exception as e:
            logger.error(f"Error clearing {flag_name} flag for IMEI {imei}: {e}")

# Global message handler instance
message_handler = MessageHandler()