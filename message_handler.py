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
            
            # Create vehicle data record
            vehicle_data = VehicleData(
                imei=imei,
                longitude=parsed_data.get('longitude'),
                latitude=parsed_data.get('latitude'),
                altitude=parsed_data.get('altitude'),
                speed=parsed_data.get('speed'),
                course=parsed_data.get('course'),
                ignition=parsed_data.get('ignition'),
                battery_level=parsed_data.get('battery_level'),
                gsm_signal=parsed_data.get('gsm_signal'),
                gps_accuracy=parsed_data.get('gps_accuracy'),
                device_timestamp=parsed_data.get('device_timestamp'),
                message_type=parsed_data.get('message_type'),
                report_type=parsed_data.get('report_type'),
                mensagem_raw=raw_message,
                client_ip=client_ip,
                server_timestamp=datetime.utcnow()
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
            
            # Prepare vehicle data
            vehicle_data = {
                'imei': imei,
                'current_ip': client_ip,
                'last_raw_message': raw_message,
                'last_update': datetime.utcnow()
            }
            
            # Update ignition status if available
            if 'ignition' in parsed_data:
                vehicle_data['ignition_status'] = parsed_data['ignition']
                if parsed_data['ignition']:
                    logger.info(f"Ignition ON detected for IMEI {imei}")
                else:
                    logger.info(f"Ignition OFF detected for IMEI {imei}")
            
            # Update battery level if available
            if parsed_data.get('battery_level'):
                vehicle_data['battery_level'] = parsed_data['battery_level']
                # Simple battery level logging
                try:
                    battery_level = float(parsed_data['battery_level'])
                    if battery_level < 10:
                        logger.warning(f"Critical battery level for IMEI {imei}: {battery_level}%")
                    elif battery_level < 20:
                        logger.info(f"Low battery level for IMEI {imei}: {battery_level}%")
                except (ValueError, TypeError):
                    pass
            
            # Update location if available
            if parsed_data.get('latitude') and parsed_data.get('longitude'):
                vehicle_data['last_location'] = {
                    'latitude': parsed_data['latitude'],
                    'longitude': parsed_data['longitude'],
                    'timestamp': parsed_data.get('device_timestamp', str(datetime.utcnow()))
                }
            
            # Handle blocking/unblocking commands
            if parsed_data.get('report_type') == 'GTOUT':
                vehicle_data['is_blocked'] = True
                logger.info(f"Vehicle blocking command processed for IMEI {imei}")
            
            # Merge with existing data if available
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None:
                        vehicle_data[key] = value
            
            # Create vehicle object and save
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            
        except Exception as e:
            logger.error(f"Error updating vehicle info for IMEI {parsed_data.get('imei')}: {e}", exc_info=True)

# Global message handler instance
message_handler = MessageHandler()