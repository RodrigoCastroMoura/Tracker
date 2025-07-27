from datetime import datetime
from typing import Dict, Optional, Any
from database import db_manager
from protocol_parser import protocol_parser
from logger import logger
from models import VehicleData, Vehicle

class MessageHandler:
    """Handle parsed messages and update database - apenas duas tabelas"""
    
    def __init__(self):
        self.device_ips = {}  # Track IP addresses for simple IP change detection
    
    def handle_incoming_message(self, raw_message: str, client_ip: str) -> Optional[str]:
        """Handle incoming GPS device message - simplified for 2 tables only"""
        try:
            # Parse the raw message
            parsed_data = protocol_parser.parse_message(raw_message)
            
            if not parsed_data:
                logger.warning(f"Unable to parse message from {client_ip}: {raw_message[:100]}...")
                return None
            
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning(f"No IMEI found in message from {client_ip}")
                return None
            
            # Log basic IP change detection
            if imei in self.device_ips and self.device_ips[imei] != client_ip:
                logger.info(f"IP change detected for IMEI {imei}: {self.device_ips[imei]} -> {client_ip}")
            self.device_ips[imei] = client_ip
            
            # Create vehicle data record - apenas dados de localização
            current_time = datetime.utcnow()
            vehicle_data = VehicleData(
                imei=imei,
                longitude=parsed_data.get('longitude'),
                latitude=parsed_data.get('latitude'),
                altitude=parsed_data.get('altitude'),
                timestamp=current_time,  # Data do servidor
                deviceTimestamp=parsed_data.get('device_timestamp', ''),  # Data do dispositivo apenas para referência
                mensagem_raw=raw_message
            )
            
            # Save vehicle data
            db_manager.insert_vehicle_data(vehicle_data)
            
            # Update vehicle information
            self._update_vehicle_info(parsed_data, client_ip, raw_message)
            
            # Generate and return acknowledgment
            response = protocol_parser.generate_acknowledgment(parsed_data)
            if response:
                logger.log_outgoing_message(client_ip, imei, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message from {client_ip}: {e}", exc_info=True)
            return None
    
    def _update_vehicle_info(self, parsed_data: Dict[str, Any], client_ip: str, raw_message: str):
        """Update vehicle information in vehicles table"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                return
            
            # Get existing vehicle or create new one
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            # Prepare vehicle data with new structure
            vehicle_data = {
                'IMEI': imei,
                'tsusermanu': datetime.utcnow()
            }
            
            # Update ignition status if available
            if 'ignition' in parsed_data:
                vehicle_data['ignicao'] = parsed_data['ignition']
                if parsed_data['ignition']:
                    logger.info(f"Ignition ON detected for IMEI {imei}")
                else:
                    logger.info(f"Ignition OFF detected for IMEI {imei}")
            
            # Update battery level if available
            if parsed_data.get('battery_level'):
                try:
                    battery_voltage = float(parsed_data['battery_level'])
                    vehicle_data['bateriavoltagem'] = battery_voltage
                    
                    # Check for low battery
                    if battery_voltage < 10.0:
                        vehicle_data['bateriabaixa'] = True
                        vehicle_data['ultimoalertabateria'] = datetime.utcnow()
                        logger.warning(f"Critical battery level for IMEI {imei}: {battery_voltage}V")
                    elif battery_voltage < 12.0:
                        vehicle_data['bateriabaixa'] = True
                        logger.info(f"Low battery level for IMEI {imei}: {battery_voltage}V")
                    else:
                        vehicle_data['bateriabaixa'] = False
                except (ValueError, TypeError):
                    pass
            
            # Handle blocking/unblocking commands
            if parsed_data.get('report_type') == 'GTOUT':
                # Process blocking command response
                if parsed_data.get('command_result'):
                    vehicle_data['bloqueado'] = True
                    vehicle_data['comandobloqueo'] = None  # Clear pending command
                    logger.info(f"Vehicle blocking command confirmed for IMEI {imei}")
            
            # Merge with existing data if available
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
            
            # Create vehicle object and save
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            
        except Exception as e:
            logger.error(f"Error updating vehicle info for IMEI {parsed_data.get('imei')}: {e}", exc_info=True)

    def save_vehicle_data(self, vehicle_data: Dict[str, Any]):
        """Save vehicle data to database - C# style method"""
        try:
            # Convert dict to VehicleData object
            current_time = datetime.utcnow()
            
            vehicle_record = VehicleData(
                imei=vehicle_data.get('imei', ''),
                longitude=vehicle_data.get('longitude', '0'),
                latitude=vehicle_data.get('latitude', '0'),
                altitude=vehicle_data.get('altitude', '0'),
                timestamp=current_time,  # Data do servidor
                deviceTimestamp=vehicle_data.get('device_timestamp', ''),  # Data do dispositivo apenas para referência
                mensagem_raw=vehicle_data.get('raw_message', '')
            )
            
            db_manager.insert_vehicle_data(vehicle_record)
            logger.debug(f"Saved vehicle data for IMEI: {vehicle_data.get('imei')}")
            
        except Exception as e:
            logger.error(f"Error saving vehicle data: {e}")
    
    def update_vehicle_ignition(self, imei: str, ignition_status: bool):
        """Update vehicle ignition status - new structure"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            # Merge with existing data
            vehicle_data = {'IMEI': imei, 'ignicao': ignition_status, 'tsusermanu': datetime.utcnow()}
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            logger.info(f"Updated ignition status for {imei}: {ignition_status}")
        except Exception as e:
            logger.error(f"Error updating vehicle ignition: {e}")
    
    def update_vehicle_blocking(self, imei: str, blocked: bool):
        """Update vehicle blocking status - new structure with command logic"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            # Merge with existing data
            vehicle_data = {'IMEI': imei, 'bloqueado': blocked, 'comandobloqueo': None, 'tsusermanu': datetime.utcnow()}
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            logger.info(f"Updated blocking status for {imei}: {'blocked' if blocked else 'unblocked'}")
        except Exception as e:
            logger.error(f"Error updating vehicle blocking: {e}")
    
    def set_blocking_command(self, imei: str, should_block: bool):
        """Set pending blocking command for vehicle"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            # Merge with existing data
            vehicle_data = {'IMEI': imei, 'comandobloqueo': should_block, 'tsusermanu': datetime.utcnow()}
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            logger.info(f"Set blocking command for {imei}: {'block' if should_block else 'unblock'}")
        except Exception as e:
            logger.error(f"Error setting blocking command: {e}")
    
    def set_ip_change_command(self, imei: str):
        """Set pending IP change command for vehicle"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            # Merge with existing data
            vehicle_data = {'IMEI': imei, 'comandotrocarip': True, 'tsusermanu': datetime.utcnow()}
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
                        
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            logger.info(f"Set IP change command for {imei}")
        except Exception as e:
            logger.error(f"Error setting IP change command: {e}")

# Global message handler instance
message_handler = MessageHandler()