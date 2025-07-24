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
            
            # Create vehicle data record - apenas campos solicitados
            current_time = datetime.utcnow()
            vehicle_data = VehicleData(
                imei=imei,
                longitude=parsed_data.get('longitude'),
                latitude=parsed_data.get('latitude'),
                altitude=parsed_data.get('altitude'),
                speed=parsed_data.get('speed'),
                ignition=parsed_data.get('ignition'),
                battery_level=parsed_data.get('battery_level'),
                timestamp=current_time,
                deviceTimestamp=parsed_data.get('device_timestamp', ''),
                systemDate=current_time,
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
                speed=vehicle_data.get('speed', '0'),
                ignition=vehicle_data.get('ignition'),
                battery_level=None,
                timestamp=current_time,
                deviceTimestamp=vehicle_data.get('device_timestamp', ''),
                systemDate=current_time,
                mensagem_raw=vehicle_data.get('raw_message', '')
            )
            
            db_manager.insert_vehicle_data(vehicle_record)
            logger.debug(f"Saved vehicle data for IMEI: {vehicle_data.get('imei')}")
            
        except Exception as e:
            logger.error(f"Error saving vehicle data: {e}")
    
    def update_vehicle_ignition(self, imei: str, ignition_status: bool):
        """Update vehicle ignition status - C# style method"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            if existing_vehicle:
                vehicle_data = {
                    'imei': imei,
                    'ignition_status': ignition_status,
                    'last_update': datetime.utcnow()
                }
                vehicle = Vehicle(**vehicle_data)
                db_manager.upsert_vehicle(vehicle)
                logger.info(f"Updated ignition status for {imei}: {ignition_status}")
        except Exception as e:
            logger.error(f"Error updating vehicle ignition: {e}")
    
    def update_vehicle_blocking(self, imei: str, blocked: bool):
        """Update vehicle blocking status - C# style method"""
        try:
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            if existing_vehicle:
                vehicle_data = {
                    'imei': imei,
                    'is_blocked': blocked,
                    'blocked_reason': "Remote command" if blocked else None,
                    'last_update': datetime.utcnow()
                }
                vehicle = Vehicle(**vehicle_data)
                db_manager.upsert_vehicle(vehicle)
                logger.info(f"Updated blocking status for {imei}: {'blocked' if blocked else 'unblocked'}")
        except Exception as e:
            logger.error(f"Error updating vehicle blocking: {e}")
    
    def update_vehicle_heartbeat(self, imei: str, timestamp: str):
        """Update vehicle heartbeat to keep connection active - C# style method"""
        try:
            # Parse timestamp if provided
            device_time = None
            if timestamp and len(timestamp) >= 14:
                try:
                    year = timestamp[0:4]
                    month = timestamp[4:6]
                    day = timestamp[6:8]
                    hour = timestamp[8:10]
                    minute = timestamp[10:12]
                    second = timestamp[12:14]
                    device_time = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                except:
                    device_time = None
            
            # Update vehicle last seen time
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            current_time = datetime.utcnow()
            
            vehicle_data = {
                'imei': imei,
                'last_seen': current_time,
                'last_heartbeat': device_time if device_time else current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'connection_status': 'active',
                'last_update': current_time
            }
            
            # Preserve existing data if vehicle exists
            if existing_vehicle:
                for key, value in existing_vehicle.items():
                    if key not in vehicle_data and value is not None and key != '_id':
                        vehicle_data[key] = value
            
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            
        except Exception as e:
            logger.error(f"Error updating vehicle heartbeat: {e}")

# Global message handler instance
message_handler = MessageHandler()