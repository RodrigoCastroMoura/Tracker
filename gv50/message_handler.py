import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
from database import db_manager
from protocol_parser import protocol_parser
from logger import logger
from models import VehicleData
from datetime_converter import convert_device_timestamp
from notification_service import notification_service


class MessageHandler:
    """Handle parsed messages and update database - async compatible"""
    
    def __init__(self):
        self.device_ips = {}
        self.pending_commands = {}
    
    def handle_incoming_message(self, raw_message: str, client_ip: str) -> Optional[str]:
        """Handle incoming GPS device message (sync version for compatibility)"""
        try:
            parsed_data = protocol_parser.parse_message(raw_message)
            
            if not parsed_data:
                logger.warning(f"Unable to parse message from {client_ip}: {raw_message[:100]}...")
                return None
            
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning(f"No IMEI found in message from {client_ip}")
                return None
            
            if imei in self.device_ips and self.device_ips[imei] != client_ip:
                logger.info(f"IP change detected for IMEI {imei}: {self.device_ips[imei]} -> {client_ip}")
            self.device_ips[imei] = client_ip
            
            current_time = datetime.now()
            
            device_timestamp_str = parsed_data.get('device_timestamp', '')
            device_datetime_converted = convert_device_timestamp(device_timestamp_str)
            
            vehicle_data = VehicleData(
                imei=imei,
                longitude=parsed_data.get('longitude'),
                latitude=parsed_data.get('latitude'),
                altitude=parsed_data.get('altitude'),
                timestamp=current_time,
                deviceTimestamp=device_datetime_converted,
                mensagem_raw=raw_message
            )
            
            db_manager.insert_vehicle_data(vehicle_data)
            
            self._update_vehicle_info(parsed_data, client_ip, raw_message)
            
            response = protocol_parser.generate_acknowledgment(parsed_data)
            if response:
                logger.log_outgoing_message(client_ip, imei, response)
            
            self._execute_command_logic(imei, client_ip)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message from {client_ip}: {e}", exc_info=True)
            return None
    
    async def handle_incoming_message_async(self, raw_message: str, client_ip: str) -> Optional[str]:
        """Handle incoming GPS device message (async version)"""
        return await asyncio.to_thread(self.handle_incoming_message, raw_message, client_ip)
    
    def _update_vehicle_info(self, parsed_data: Dict[str, Any], client_ip: str, raw_message: str):
        """Update vehicle information in vehicles table"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                return
            
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            placa = existing_vehicle.get('dsplaca') if existing_vehicle else None
            
            vehicle_data = {
                'IMEI': imei,
                'tsusermanu': datetime.now()
            }
            
            if 'ignition' in parsed_data:
                vehicle_data['ignicao'] = parsed_data['ignition']
                
                if parsed_data['ignition']:
                    logger.info(f"Ignition ON detected for IMEI {imei}")
                    notification_service.notify_ignition_on(imei, placa)
                else:
                    logger.info(f"Ignition OFF detected for IMEI {imei}")
                    notification_service.notify_ignition_off(imei, placa)
            
            if parsed_data.get('battery_level'):
                try:
                    battery_voltage = float(parsed_data['battery_level'])
                    vehicle_data['bateriavoltagem'] = battery_voltage
                    
                    if battery_voltage < 10.0:
                        vehicle_data['bateriabaixa'] = True
                        vehicle_data['ultimoalertabateria'] = datetime.now()
                        logger.warning(f"Critical battery level for IMEI {imei}: {battery_voltage}V")
                        notification_service.notify_low_battery(imei, battery_voltage, placa)
                    elif battery_voltage < 12.0:
                        vehicle_data['bateriabaixa'] = True
                        logger.info(f"Low battery level for IMEI {imei}: {battery_voltage}V")
                    else:
                        vehicle_data['bateriabaixa'] = False
                except (ValueError, TypeError):
                    pass
            
            if parsed_data.get('report_type') == 'GTOUT':
                is_blocked = parsed_data.get('blocked', False)
                
                vehicle_data['bloqueado'] = is_blocked
                vehicle_data['comandobloqueo'] = None
                
                if is_blocked:
                    logger.info(f"Vehicle blocking command confirmed for IMEI {imei}")
                    notification_service.notify_vehicle_blocked(imei, placa)
                else:
                    logger.info(f"Vehicle unblocking command confirmed for IMEI {imei}")
                    notification_service.notify_vehicle_unblocked(imei, placa)
            
            if parsed_data.get('report_type') == 'GTSRI':
                ip_change_success = parsed_data.get('ip_change_success', False)
                if ip_change_success:
                    logger.info(f"IP change command confirmed for IMEI {imei}")
                else:
                    logger.warning(f"IP change command failed for IMEI {imei}: status {parsed_data.get('status', 'unknown')}")
            
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
            
            db_manager.upsert_vehicle(vehicle_data)
            
        except Exception as e:
            logger.error(f"Error updating vehicle info for IMEI {parsed_data.get('imei')}: {e}", exc_info=True)
    
    async def _update_vehicle_info_async(self, parsed_data: Dict[str, Any], client_ip: str, raw_message: str):
        """Update vehicle information (async version)"""
        return await asyncio.to_thread(self._update_vehicle_info, parsed_data, client_ip, raw_message)
    
    def _execute_command_logic(self, imei: str, client_ip: str):
        """Execute command logic - C# style Command() function"""
        try:
            veiculo = db_manager.get_vehicle_by_imei(imei)
            
            if veiculo is None:
                return
            
            comando_pendente = veiculo.get('comandobloqueo')
            if comando_pendente is not None:
                if comando_pendente == True:
                    bit = "1"
                else:
                    bit = "0"
                
                comando = f"AT+GTOUT=gv50,{bit},,,,,,0,,,,,,,000{bit}$"
                
                self._send_command_to_device(comando, client_ip, imei)
                
        except Exception as e:
            logger.error(f"Error in command logic for {imei}: {e}")
    
    async def _execute_command_logic_async(self, imei: str, client_ip: str):
        """Execute command logic (async version)"""
        return await asyncio.to_thread(self._execute_command_logic, imei, client_ip)
    
    def _send_command_to_device(self, command: str, client_ip: str, imei: str):
        """Prepare command for device"""
        try:
            if imei not in self.pending_commands:
                self.pending_commands[imei] = []
            
            self.pending_commands[imei].append(command)
            
        except Exception as e:
            logger.error(f"Error preparing command: {e}")
    
    def get_pending_command(self, imei: str) -> Optional[str]:
        """Get pending command for TCP server"""
        try:
            if imei in self.pending_commands:
                if self.pending_commands[imei]:
                    command = self.pending_commands[imei].pop(0)
                    return command
            return None
        except Exception as e:
            logger.error(f"Error getting pending command: {e}")
            return None

    def save_vehicle_data(self, vehicle_data: Dict[str, Any]):
        """Save vehicle data to database (sync version)"""
        try:
            current_time = datetime.now()
            
            device_timestamp_str = vehicle_data.get('device_timestamp', '')
            device_datetime_converted = convert_device_timestamp(device_timestamp_str)
          
            vehicle_record = VehicleData(
                imei=vehicle_data.get('imei', ''),
                longitude=vehicle_data.get('longitude', '0'),
                latitude=vehicle_data.get('latitude', '0'),
                altitude=vehicle_data.get('altitude', '0'),
                timestamp=current_time,
                deviceTimestamp=device_datetime_converted,
                mensagem_raw=vehicle_data.get('raw_message', '')
            )
            
            db_manager.insert_vehicle_data(vehicle_record)
            
        except Exception as e:
            logger.error(f"Error saving vehicle data: {e}")
    
    async def save_vehicle_data_async(self, vehicle_data: Dict[str, Any]):
        """Save vehicle data to database (async version)"""
        return await asyncio.to_thread(self.save_vehicle_data, vehicle_data)
    
    def update_vehicle_ignition(self, imei: str, ignition_status: bool):
        """Update vehicle ignition status (sync version)"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            vehicle_data = {'IMEI': imei, 'ignicao': ignition_status, 'tsusermanu': datetime.now()}
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            db_manager.upsert_vehicle(vehicle_data)
        except Exception as e:
            logger.error(f"Error updating vehicle ignition: {e}")
    
    async def update_vehicle_ignition_async(self, imei: str, ignition_status: bool):
        """Update vehicle ignition status (async version)"""
        return await asyncio.to_thread(self.update_vehicle_ignition, imei, ignition_status)
    
    def update_vehicle_blocking(self, imei: str, blocked: bool):
        """Update vehicle blocking status after ACK confirmation (sync version)"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            vehicle_data = {
                'IMEI': imei, 
                'bloqueado': blocked, 
                'comandobloqueo': None,
                'tsusermanu': datetime.now()
            }
            
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            db_manager.upsert_vehicle(vehicle_data)
            logger.info(f"Updated blocking status for {imei}: {'blocked' if blocked else 'unblocked'}")
            
            placa = existing_vehicle.get('dsplaca') if existing_vehicle else None
            if blocked:
                notification_service.notify_vehicle_blocked(imei, placa)
            else:
                notification_service.notify_vehicle_unblocked(imei, placa)
        except Exception as e:
            logger.error(f"Error updating vehicle blocking status: {e}")
    
    async def update_vehicle_blocking_async(self, imei: str, blocked: bool):
        """Update vehicle blocking status (async version)"""
        return await asyncio.to_thread(self.update_vehicle_blocking, imei, blocked)
    
    def set_blocking_command(self, imei: str, should_block: bool):
        """Set pending blocking command for vehicle (sync version)"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            vehicle_data = {'IMEI': imei, 'comandobloqueo': should_block, 'tsusermanu': datetime.now()}
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            db_manager.upsert_vehicle(vehicle_data)
            logger.info(f"Set blocking command for {imei}: {'block' if should_block else 'unblock'}")
        except Exception as e:
            logger.error(f"Error setting blocking command: {e}")
    
    async def set_blocking_command_async(self, imei: str, should_block: bool):
        """Set pending blocking command (async version)"""
        return await asyncio.to_thread(self.set_blocking_command, imei, should_block)
    
    def set_ip_change_command(self, imei: str):
        """Set pending IP change command for vehicle (sync version)"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            vehicle_data = {'IMEI': imei, 'comandotrocarip': True, 'tsusermanu': datetime.now()}
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            db_manager.upsert_vehicle(vehicle_data)
            logger.info(f"Set IP change command for {imei}")
        except Exception as e:
            logger.error(f"Error setting IP change command: {e}")
    
    async def set_ip_change_command_async(self, imei: str):
        """Set IP change command (async version)"""
        return await asyncio.to_thread(self.set_ip_change_command, imei)
    
    def update_vehicle_motion_status(self, imei: str, motion_status: str):
        """Update vehicle motion status based on GTSTT message (sync version)"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            motion_descriptions = {
                '11': 'Start Moving',
                '12': 'Stop Moving', 
                '21': 'Start Moving (Vibration)',
                '22': 'Stop Moving (Vibration)',
                '41': 'Sensor Rest',
                '42': 'Sensor Motion'
            }
            
            motion_description = motion_descriptions.get(motion_status, f'Unknown Status ({motion_status})')
            is_moving = motion_status in ['11', '21', '42']
            
            vehicle_data = {
                'IMEI': imei, 
                'motion_status': motion_status,
                'motion_description': motion_description,
                'is_moving': is_moving,
                'tsusermanu': datetime.now()
            }
            
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            db_manager.upsert_vehicle(vehicle_data)
            logger.info(f"Updated motion status for {imei}: {motion_description} (status: {motion_status})")
            
        except Exception as e:
            logger.error(f"Error updating vehicle motion status: {e}")
    
    async def update_vehicle_motion_status_async(self, imei: str, motion_status: str):
        """Update vehicle motion status (async version)"""
        return await asyncio.to_thread(self.update_vehicle_motion_status, imei, motion_status)


message_handler = MessageHandler()
