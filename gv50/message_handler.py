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
            
            # Command execution is now handled by TCP server directly
            
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
                    
                    # Fix field name compatibility
                    if 'imei' in vehicle_data and 'IMEI' not in vehicle_data:
                        vehicle_data['IMEI'] = vehicle_data['imei']
                        del vehicle_data['imei']
                    
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
                    
                    # Fix field name compatibility
                    if 'imei' in vehicle_data and 'IMEI' not in vehicle_data:
                        vehicle_data['IMEI'] = vehicle_data['imei']
                        del vehicle_data['imei']
                    
                    updated_vehicle = Vehicle(**vehicle_data)
                    db_manager.upsert_vehicle(updated_vehicle)
                    logger.debug(f"Ignition OFF updated for IMEI: {imei}")
            
            # Process ACK responses for command confirmation
            elif report_type == 'GTOUT' and parsed_data.get('msg_type') == 'ACK':
                self._process_gtout_ack(imei, parsed_data, raw_message)
                    
        except Exception as e:
            logger.error(f"Error updating vehicle: {e}")
    
    def _process_gtout_ack(self, imei: str, parsed_data: Dict[str, Any], raw_message: str):
        """Process GTOUT ACK response to update blocking status"""
        try:
            # Check if this is a successful ACK (status 0001, 0002, or 0003)
            status = parsed_data.get('status', '')
            if status in ['0001', '0002', '0003']:  # Successful command execution
                
                vehicle = db_manager.get_vehicle_by_imei(imei)
                if vehicle:
                    vehicle_data = dict(vehicle)
                    if '_id' in vehicle_data:
                        del vehicle_data['_id']
                    
                    # Check what type of command was pending to determine the result
                    current_command = vehicle_data.get('comandobloqueo')
                    if current_command is True:
                        # This was a blocking command confirmation
                        vehicle_data['bloqueado'] = True
                        vehicle_data['comandobloqueo'] = None  # Clear pending command
                        logger.info(f"✅ Bloqueio confirmado para IMEI {imei} - Status: {status}")
                    elif current_command is False:
                        # This was an unblocking command confirmation
                        vehicle_data['bloqueado'] = False
                        vehicle_data['comandobloqueo'] = None  # Clear pending command
                        logger.info(f"✅ Desbloqueio confirmado para IMEI {imei} - Status: {status}")
                    else:
                        # Fallback: try to determine from ACK message content
                        # Look for status field in GTOUT ACK which indicates result
                        if parsed_data.get('blocked', False):  # From GTOUT parser
                            vehicle_data['bloqueado'] = True
                            logger.info(f"✅ Bloqueio confirmado (ACK) para IMEI {imei} - Status: {status}")
                        else:
                            vehicle_data['bloqueado'] = False
                            logger.info(f"✅ Desbloqueio confirmado (ACK) para IMEI {imei} - Status: {status}")
                        vehicle_data['comandobloqueo'] = None
                    
                    vehicle_data['tsusermanu'] = datetime.utcnow()
                    
                    # Fix field name compatibility - Vehicle model expects IMEI (uppercase)
                    if 'imei' in vehicle_data and 'IMEI' not in vehicle_data:
                        vehicle_data['IMEI'] = vehicle_data['imei']
                        del vehicle_data['imei']
                    
                    from models import Vehicle
                    updated_vehicle = Vehicle(**vehicle_data)
                    db_manager.upsert_vehicle(updated_vehicle)
                    
            else:
                logger.warning(f"GTOUT command failed for IMEI {imei} - Status: {status}")
                
        except Exception as e:
            logger.error(f"Error processing GTOUT ACK for IMEI {imei}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    # Command execution removed - now handled exclusively by TCP server

# Global message handler instance
message_handler = MessageHandler()