from datetime import datetime
from typing import Dict, Optional, Any
from database import db_manager
from protocol_parser import protocol_parser
from logger import logger
from models import VehicleData, Vehicle, EventLog, MessageLog, IPChangeLog, BatteryEvent

class MessageHandler:
    """Handle parsed messages and update database accordingly"""
    
    def __init__(self):
        pass
    
    def process_message(self, parsed_data: Dict[str, Any], client_ip: str) -> Optional[str]:
        """Process parsed message and return acknowledgment if needed"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Received message without IMEI")
                return None
            
            # Log the message
            self._log_message(parsed_data, client_ip, 'incoming')
            
            # Check for IP changes
            self._check_ip_change(imei, client_ip)
            
            # Process based on message type
            message_type = parsed_data.get('message_type')
            report_type = parsed_data.get('report_type')
            
            if message_type in ['+RESP', '+BUFF']:
                self._handle_report_message(parsed_data, client_ip)
            elif message_type == '+ACK':
                self._handle_acknowledgment_message(parsed_data, client_ip)
            
            # Generate acknowledgment response
            ack_response = protocol_parser.generate_acknowledgment(parsed_data)
            
            if ack_response:
                # Log outgoing message
                self._log_outgoing_message(imei, client_ip, ack_response)
            
            return ack_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return None
    
    def _handle_report_message(self, parsed_data: Dict[str, Any], client_ip: str):
        """Handle report messages (+RESP and +BUFF)"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Report message received without IMEI")
                return
                
            report_type = parsed_data.get('report_type')
            
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
                server_timestamp=datetime.utcnow(),
                raw_message=parsed_data.get('raw_message'),
                mensagem_raw=parsed_data.get('raw_message'),
                message_type=parsed_data.get('message_type'), 
                report_type=report_type
            )
            
            # Insert vehicle data
            db_manager.insert_vehicle_data(vehicle_data)
            
            # Update vehicle information
            self._update_vehicle_info(parsed_data)
            
            # Handle specific report types
            if report_type in ['GTIGN', 'GTIGF']:
                self._handle_ignition_event(parsed_data)
            elif report_type == 'GTPFA':
                self._handle_power_off_event(parsed_data)
            elif report_type == 'GTPNA':
                self._handle_power_on_event(parsed_data)
            elif report_type in ['GTSOS', 'GTGEO', 'GTSPD']:
                self._handle_alert_event(parsed_data)
            
        except Exception as e:
            logger.error(f"Error handling report message: {e}", exc_info=True)
    
    def _handle_acknowledgment_message(self, parsed_data: Dict[str, Any], client_ip: str):
        """Handle acknowledgment messages (+ACK)"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("ACK message received without IMEI")
                return
                
            report_type = parsed_data.get('report_type')
            
            if report_type == 'GTOUT':
                self._handle_output_acknowledgment(parsed_data)
            
            # Log the acknowledgment
            event_log = EventLog(
                imei=imei,
                event_type='acknowledgment_received',
                event_data={
                    'report_type': report_type,
                    'output_status': parsed_data.get('output_status')
                },
                raw_message=parsed_data.get('raw_message')
            )
            
            db_manager.insert_event_log(event_log)
            
        except Exception as e:
            logger.error(f"Error handling acknowledgment message: {e}", exc_info=True)
    
    def _update_vehicle_info(self, parsed_data: Dict[str, Any]):
        """Update vehicle information in database"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Cannot update vehicle info without IMEI")
                return
            
            # Get existing vehicle or create new one
            existing_vehicle = db_manager.get_vehicle_by_imei(imei)
            
            vehicle_data = {
                'imei': imei,
                'last_location': {
                    'longitude': parsed_data.get('longitude'),
                    'latitude': parsed_data.get('latitude'),
                    'altitude': parsed_data.get('altitude')
                } if parsed_data.get('longitude') and parsed_data.get('latitude') else None,
                'last_update': datetime.utcnow(),
                'last_raw_message': parsed_data.get('raw_message')
            }
            
            # Update ignition status if available
            if 'ignition' in parsed_data:
                vehicle_data['ignition_status'] = parsed_data['ignition']
            
            # Update battery level if available and handle battery events
            if parsed_data.get('battery_level'):
                vehicle_data['battery_level'] = parsed_data['battery_level']
                self._handle_battery_event(parsed_data)
            
            # Merge with existing data
            if existing_vehicle:
                vehicle_data.update({
                    'plate_number': existing_vehicle.get('plate_number'),
                    'model': existing_vehicle.get('model'),
                    'year': existing_vehicle.get('year'),
                    'owner_cpf': existing_vehicle.get('owner_cpf'),
                    'chip_number': existing_vehicle.get('chip_number'),
                    'is_blocked': existing_vehicle.get('is_blocked', False),
                    'block_command_pending': existing_vehicle.get('block_command_pending', False),
                    'block_notification_sent': existing_vehicle.get('block_notification_sent', False),
                    'status': existing_vehicle.get('status', 'active'),
                    'created_at': existing_vehicle.get('created_at')
                })
            
            vehicle = Vehicle(**vehicle_data)
            db_manager.upsert_vehicle(vehicle)
            
        except Exception as e:
            logger.error(f"Error updating vehicle info: {e}", exc_info=True)
    
    def _handle_ignition_event(self, parsed_data: Dict[str, Any]):
        """Handle ignition on/off events"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Cannot handle ignition event without IMEI")
                return
                
            report_type = parsed_data.get('report_type')
            ignition_status = parsed_data.get('ignition')
            
            event_type = 'ignition_on' if ignition_status else 'ignition_off'
            
            event_log = EventLog(
                imei=imei,
                event_type=event_type,
                event_data={
                    'ignition_status': ignition_status,
                    'location': {
                        'longitude': parsed_data.get('longitude'),
                        'latitude': parsed_data.get('latitude')
                    }
                },
                raw_message=parsed_data.get('raw_message')
            )
            
            db_manager.insert_event_log(event_log)
            logger.info(f"Ignition event processed for IMEI {imei}: {event_type}")
            
        except Exception as e:
            logger.error(f"Error handling ignition event: {e}", exc_info=True)
    
    def _handle_power_off_event(self, parsed_data: Dict[str, Any]):
        """Handle power off event"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Cannot handle power off event without IMEI")
                return
            
            event_log = EventLog(
                imei=imei,
                event_type='power_off',
                event_data={
                    'location': {
                        'longitude': parsed_data.get('longitude'),
                        'latitude': parsed_data.get('latitude')
                    }
                },
                raw_message=parsed_data.get('raw_message')
            )
            
            db_manager.insert_event_log(event_log)
            logger.info(f"Power off event processed for IMEI {imei}")
            
        except Exception as e:
            logger.error(f"Error handling power off event: {e}", exc_info=True)
    
    def _handle_power_on_event(self, parsed_data: Dict[str, Any]):
        """Handle power on event"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Cannot handle power on event without IMEI")
                return
            
            event_log = EventLog(
                imei=imei,
                event_type='power_on',
                event_data={
                    'location': {
                        'longitude': parsed_data.get('longitude'),
                        'latitude': parsed_data.get('latitude')
                    }
                },
                raw_message=parsed_data.get('raw_message')
            )
            
            db_manager.insert_event_log(event_log)
            logger.info(f"Power on event processed for IMEI {imei}")
            
        except Exception as e:
            logger.error(f"Error handling power on event: {e}", exc_info=True)
    
    def _handle_alert_event(self, parsed_data: Dict[str, Any]):
        """Handle alert events (SOS, geofence, speed, etc.)"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Cannot handle alert event without IMEI")
                return
                
            report_type = parsed_data.get('report_type')
            
            event_type_map = {
                'GTSOS': 'sos_alert',
                'GTGEO': 'geofence_alert',
                'GTSPD': 'speed_alert',
                'GTTOW': 'towing_alert',
                'GTDIS': 'disconnection_alert'
            }
            
            event_type = event_type_map.get(report_type, 'unknown_alert')
            
            event_log = EventLog(
                imei=imei,
                event_type=event_type,
                event_data={
                    'alert_type': report_type,
                    'speed': parsed_data.get('speed'),
                    'location': {
                        'longitude': parsed_data.get('longitude'),
                        'latitude': parsed_data.get('latitude')
                    }
                },
                raw_message=parsed_data.get('raw_message')
            )
            
            db_manager.insert_event_log(event_log)
            logger.info(f"Alert event processed for IMEI {imei}: {event_type}")
            
        except Exception as e:
            logger.error(f"Error handling alert event: {e}", exc_info=True)
    
    def _handle_output_acknowledgment(self, parsed_data: Dict[str, Any]):
        """Handle output control acknowledgment (block/unblock response)"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Cannot handle output acknowledgment without IMEI")
                return
                
            output_status = parsed_data.get('output_status')
            
            # Update vehicle block status
            vehicle = db_manager.get_vehicle_by_imei(imei)
            if vehicle:
                is_blocked = output_status == '0000'  # 0000 means blocked, 0001 means unblocked
                
                vehicle_update = Vehicle(
                    imei=imei,
                    plate_number=vehicle.get('plate_number'),
                    model=vehicle.get('model'),
                    year=vehicle.get('year'),
                    owner_cpf=vehicle.get('owner_cpf'),
                    chip_number=vehicle.get('chip_number'),
                    is_blocked=is_blocked,
                    block_command_pending=False,  # Command completed
                    block_notification_sent=True,
                    ignition_status=vehicle.get('ignition_status'),
                    battery_level=vehicle.get('battery_level'),
                    last_location=vehicle.get('last_location'),
                    last_raw_message=parsed_data.get('raw_message'),
                    status=vehicle.get('status', 'active'),
                    created_at=vehicle.get('created_at')
                )
                
                db_manager.upsert_vehicle(vehicle_update)
                
                # Log the block/unblock event
                event_type = 'vehicle_blocked' if is_blocked else 'vehicle_unblocked'
                event_log = EventLog(
                    imei=imei,
                    event_type=event_type,
                    event_data={
                        'output_status': output_status,
                        'is_blocked': is_blocked
                    },
                    raw_message=parsed_data.get('raw_message')
                )
                
                db_manager.insert_event_log(event_log)
                logger.info(f"Vehicle {imei} {'blocked' if is_blocked else 'unblocked'} successfully")
            
        except Exception as e:
            logger.error(f"Error handling output acknowledgment: {e}", exc_info=True)
    
    def _check_ip_change(self, imei: str, current_ip: str):
        """Check and log IP changes for device"""
        try:
            vehicle = db_manager.get_vehicle_by_imei(imei)
            
            if vehicle:
                last_ip = vehicle.get('last_ip')
                
                if last_ip and last_ip != current_ip:
                    # Log IP change
                    ip_change_log = IPChangeLog(
                        imei=imei,
                        old_ip=last_ip,
                        new_ip=current_ip,
                        change_reason='device_reconnection'
                    )
                    
                    db_manager.insert_ip_change_log(ip_change_log)
                    logger.info(f"IP change detected for IMEI {imei}: {last_ip} -> {current_ip}")
                
                # Update vehicle with new IP
                if 'last_ip' not in vehicle or vehicle['last_ip'] != current_ip:
                    vehicle_update = Vehicle(
                        imei=imei,
                        plate_number=vehicle.get('plate_number'),
                        model=vehicle.get('model'),
                        year=vehicle.get('year'),
                        owner_cpf=vehicle.get('owner_cpf'),
                        chip_number=vehicle.get('chip_number'),
                        is_blocked=vehicle.get('is_blocked', False),
                        block_command_pending=vehicle.get('block_command_pending', False),
                        block_notification_sent=vehicle.get('block_notification_sent', False),
                        ignition_status=vehicle.get('ignition_status'),
                        battery_level=vehicle.get('battery_level'),
                        last_location=vehicle.get('last_location'),
                        last_raw_message=vehicle.get('last_raw_message'),
                        status=vehicle.get('status', 'active'),
                        created_at=vehicle.get('created_at')
                    )
                    vehicle_update_dict = vehicle_update.to_dict()
                    vehicle_update_dict['last_ip'] = current_ip
                    
                    # Manual update to include last_ip
                    if db_manager.db:
                        db_manager.db['vehicles'].update_one(
                            {'imei': imei},
                            {'$set': vehicle_update_dict},
                        upsert=True
                    )
            
        except Exception as e:
            logger.error(f"Error checking IP change: {e}", exc_info=True)
    
    def _log_message(self, parsed_data: Dict[str, Any], client_ip: str, direction: str):
        """Log message to database"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                return
            
            message_log = MessageLog(
                imei=imei,
                client_ip=client_ip,
                message_direction=direction,
                raw_message=parsed_data.get('raw_message', ''),
                message_type=parsed_data.get('message_type'),
                report_type=parsed_data.get('report_type'),
                parsed_data=parsed_data
            )
            
            db_manager.insert_message_log(message_log)
            logger.log_incoming_message(client_ip, imei, parsed_data.get('raw_message', ''))
            
        except Exception as e:
            logger.error(f"Error logging message: {e}", exc_info=True)
    
    def _log_outgoing_message(self, imei: str, client_ip: str, response: str):
        """Log outgoing message"""
        try:
            message_log = MessageLog(
                imei=imei,
                client_ip=client_ip,
                message_direction='outgoing',
                raw_message=response,
                message_type='ACK',
                report_type='RESPONSE'
            )
            
            db_manager.insert_message_log(message_log)
            logger.log_outgoing_message(client_ip, imei, response)
            
        except Exception as e:
            logger.error(f"Error logging outgoing message: {e}", exc_info=True)
    
    def _handle_battery_event(self, parsed_data: Dict[str, Any]):
        """Handle battery level events"""
        try:
            imei = parsed_data.get('imei')
            if not imei:
                logger.warning("Cannot handle battery event without IMEI")
                return
                
            battery_level = parsed_data.get('battery_level')
            if not battery_level:
                return
                
            # Check for low battery conditions
            try:
                battery_percentage = float(battery_level)
                low_battery = battery_percentage < 20
                critical_battery = battery_percentage < 10
            except (ValueError, TypeError):
                low_battery = False
                critical_battery = False
            
            battery_event = BatteryEvent(
                imei=imei,
                battery_level=battery_level,
                battery_voltage=parsed_data.get('battery_voltage'),
                charging_status=parsed_data.get('charging_status'),
                low_battery_alert=low_battery,
                critical_battery_alert=critical_battery,
                external_power_status=parsed_data.get('external_power_status'),
                raw_message=parsed_data.get('raw_message')
            )
            
            db_manager.insert_battery_event(battery_event)
            
            # Log battery alerts
            if critical_battery:
                event_log = EventLog(
                    imei=imei,
                    event_type='critical_battery_alert',
                    event_data={
                        'battery_level': battery_level,
                        'alert_type': 'critical'
                    },
                    raw_message=parsed_data.get('raw_message')
                )
                db_manager.insert_event_log(event_log)
                logger.warning(f"Critical battery alert for IMEI {imei}: {battery_level}%")
            elif low_battery:
                event_log = EventLog(
                    imei=imei,
                    event_type='low_battery_alert',
                    event_data={
                        'battery_level': battery_level,
                        'alert_type': 'low'
                    },
                    raw_message=parsed_data.get('raw_message')
                )
                db_manager.insert_event_log(event_log)
                logger.info(f"Low battery alert for IMEI {imei}: {battery_level}%")
            
        except Exception as e:
            logger.error(f"Error handling battery event: {e}", exc_info=True)

# Global message handler instance
message_handler = MessageHandler()
