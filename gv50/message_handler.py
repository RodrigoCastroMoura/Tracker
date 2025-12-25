#!/usr/bin/env python3
"""
Message Handler for GV50 Protocol
Processes incoming messages and generates appropriate responses
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from config import Config
from logger import logger
from database import db_manager
from models import VehicleData
from notification_service import notification_service
from datetime_converter import convert_device_timestamp


class MessageHandler:
    """Handler for GV50 protocol messages"""
    
    def __init__(self):
        self.protocol_parser = None
        self.pending_commands: Dict[str, list] = {}  # IMEI -> list of commands
    
    async def process_message(self, message: str, imei: Optional[str], client_ip: str) -> Optional[str]:
        """
        Process incoming message and return response if needed
        
        Args:
            message: Raw message from device
            imei: Device IMEI (if known)
            client_ip: Client IP address
            
        Returns:
            Response string or None
        """
        try:
            # Lazy load protocol parser to avoid circular imports
            if not self.protocol_parser:
                from protocol_parser import ProtocolParser
                self.protocol_parser = ProtocolParser()
            
            # Parse message
            parsed = self.protocol_parser.parse_message(message)
            
            if not parsed:
                logger.error(f"Failed to parse message: {message[:100]}")
                return None
            
            message_type = parsed.get('message_type')
            parsed_imei = parsed.get('imei', imei)
            
            logger.debug(f"Processing {message_type} from IMEI {parsed_imei}")
            
            # Process based on message type
            if message_type == 'GTFRI':
                await self._handle_fixed_report(parsed, message)
            elif message_type == 'GTHBD':
                await self._handle_heartbeat(parsed)
            elif message_type == 'GTIGN':
                await self._handle_ignition_on(parsed, message)
            elif message_type == 'GTIGF':
                await self._handle_ignition_off(parsed, message)
            elif message_type == 'GTOUT':
                await self._handle_output_control(parsed)
            elif message_type == 'GTEPS':
                await self._handle_external_power(parsed, message)
            elif message_type == 'GTPNA':
                await self._handle_power_on(parsed, message)
            elif message_type == 'GTPFA':
                await self._handle_power_off(parsed, message)
            elif message_type == 'GTMPN':
                await self._handle_motion_start(parsed, message)
            elif message_type == 'GTMPF':
                await self._handle_motion_stop(parsed, message)
            elif message_type == 'GTBTC':
                await self._handle_battery_start_charge(parsed, message)
            elif message_type == 'GTSTC':
                await self._handle_battery_stop_charge(parsed, message)
            elif message_type == 'GTSTT':
                await self._handle_motion_state(parsed)
            elif message_type in ['ACK_GTBSI', 'ACK_GTSRI', 'ACK_GTOUT', 
                                  'ACK_GTFRI', 'ACK_GTDOG', 'ACK_GTEPS']:
                logger.debug(f"Received ACK for {message_type}")
            else:
                logger.warning(f"Unknown message type: {message_type}")
            
            # Check for pending commands
            response = await self._check_pending_commands(parsed_imei)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return None
    
    async def _handle_fixed_report(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTFRI - Fixed Report Information"""
        try:
            imei = parsed.get('imei')
            if not imei:
                return
            
            # Check if it's a BUFF message (buffered/historical data)
            is_buff = parsed.get('category') == 'BUFF'
            
            # For BUFF messages, use device timestamp for both fields

            device_timestamp_str = parsed.get('mcc', '')
            device_datetime_converted = convert_device_timestamp(device_timestamp_str)
            device_time = device_datetime_converted
            if is_buff and device_time:
                server_time = device_time  # Use device time for historical data
            else:
                server_time = datetime.now()  # Use current time for real-time data
            
            # Create vehicle data record
            vehicle_data = VehicleData(
                imei=imei,
                longitude=parsed.get('longitude'),
                latitude=parsed.get('latitude'),
                altitude=parsed.get('altitude'),
                timestamp=server_time,
                deviceTimestamp=device_time,
                mensagem_raw=raw_message
            )
            
            # Insert to database (async)
            await db_manager.insert_vehicle_data_async(vehicle_data)
            
            # Only update Vehicle table if NOT a BUFF message
            if not is_buff:
                # Update vehicle information with location
                vehicle_update = {
                    'IMEI': imei,
                    'tsusermanu': datetime.now(),
                    'longitude': parsed.get('longitude'),
                    'latitude': parsed.get('latitude'),
                    'altitude': parsed.get('altitude')
                }
                
                # Update battery voltage if available
                if 'battery_voltage' in parsed:
                    vehicle_update['bateriavoltagem'] = float(parsed['battery_voltage'])
                
                await db_manager.upsert_vehicle_async(vehicle_update)
            else:
                logger.debug(f"BUFF message for IMEI {imei} - only saved to vehicle_data")
            
        except Exception as e:
            logger.error(f"Error handling GTFRI: {e}")
    
    async def _handle_heartbeat(self, parsed: Dict[str, Any]):
        """Handle GTHBD - Heartbeat"""
        try:
            imei = parsed.get('imei')
            if not imei:
                return
            
            # Update vehicle last activity
            vehicle_update = {
                'IMEI': imei,
                'tsusermanu': datetime.now()
            }
            
            await db_manager.upsert_vehicle_async(vehicle_update)
            
            logger.debug(f"Heartbeat processed for IMEI {imei}")
            
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
    
    async def _handle_ignition_on(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTIGN - Ignition On"""
        try:
            imei = parsed.get('imei')
            if not imei:
                return
            
            # Check if it's a BUFF message (buffered/historical data)
            is_buff = parsed.get('category') == 'BUFF'
            
            # Only update Vehicle table if NOT a BUFF message
            if not is_buff:
                # Update vehicle ignition status and location
                vehicle_update = {
                    'IMEI': imei,
                    'ignicao': True,
                    'tsusermanu': datetime.now(),
                    'longitude': parsed.get('longitude'),
                    'latitude': parsed.get('latitude'),
                    'altitude': parsed.get('altitude')
                }
                
                await db_manager.upsert_vehicle_async(vehicle_update)
                
                # Send push notification
                vehicle = await db_manager.get_vehicle_by_imei_async(imei)
                placa = vehicle.get('dsplaca') if vehicle else None
                notification_service.notify_ignition_on(imei, placa)
                
                logger.info(f"Ignition ON for IMEI {imei}")
            else:
                logger.debug(f"BUFF message GTIGN for IMEI {imei} - only saved to vehicle_data")
            
        except Exception as e:
            logger.error(f"Error handling ignition on: {e}")
    
    async def _handle_ignition_off(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTIGF - Ignition Off"""
        try:
            imei = parsed.get('imei')
            if not imei:
                return
            
            # Check if it's a BUFF message (buffered/historical data)
            is_buff = parsed.get('category') == 'BUFF'
            
            # Only update Vehicle table if NOT a BUFF message
            if not is_buff:
                # Update vehicle ignition status and location
                vehicle_update = {
                    'IMEI': imei,
                    'ignicao': False,
                    'tsusermanu': datetime.now(),
                    'longitude': parsed.get('longitude'),
                    'latitude': parsed.get('latitude'),
                    'altitude': parsed.get('altitude')
                }
                
                await db_manager.upsert_vehicle_async(vehicle_update)
                
                # Send push notification
                vehicle = await db_manager.get_vehicle_by_imei_async(imei)
                placa = vehicle.get('dsplaca') if vehicle else None
                notification_service.notify_ignition_off(imei, placa)
                
                logger.info(f"Ignition OFF for IMEI {imei}")
            else:
                logger.debug(f"BUFF message GTIGF for IMEI {imei} - only saved to vehicle_data")
            
        except Exception as e:
            logger.error(f"Error handling ignition off: {e}")
    
    async def _handle_output_control(self, parsed: Dict[str, Any]):
        """Handle GTOUT - Output Control Response"""
        try:
            imei = parsed.get('imei')
            output_status = parsed.get('output_status')
            
            if not imei or output_status is None:
                return
            
            # Update vehicle block status
            is_blocked = (output_status == 1)  # 1 = output ON = blocked
            
            vehicle_update = {
                'IMEI': imei,
                'bloqueado': is_blocked,
                'comandobloqueo': None,  # Clear pending command
                'tsusermanu': datetime.now()
            }
            
            await db_manager.upsert_vehicle_async(vehicle_update)
            
            # Send push notification
            vehicle = await db_manager.get_vehicle_by_imei_async(imei)
            placa = vehicle.get('dsplaca') if vehicle else None
            
            if is_blocked:
                notification_service.notify_vehicle_blocked(imei, placa)
            else:
                notification_service.notify_vehicle_unblocked(imei, placa)
            
            logger.info(f"Output control response for IMEI {imei}: {'blocked' if is_blocked else 'unblocked'}")
            
        except Exception as e:
            logger.error(f"Error handling output control: {e}")
    
    async def _handle_external_power(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTEPS - External Power Supply"""
        try:
            imei = parsed.get('imei')
            battery_voltage = parsed.get('battery_voltage')
            
            if not imei:
                return
            
            # Check if it's a BUFF message (buffered/historical data)
            is_buff = parsed.get('category') == 'BUFF'
                
            # Only update Vehicle table if NOT a BUFF message
            if not is_buff:
                vehicle_update = {
                    'IMEI': imei,
                    'tsusermanu': datetime.now(),
                    'longitude': parsed.get('longitude'),
                    'latitude': parsed.get('latitude'),
                    'altitude': parsed.get('altitude')
                }
                
                # Check for low battery
                if battery_voltage:
                    voltage = float(battery_voltage)
                    vehicle_update['bateriavoltagem'] = voltage
                    
                    # Low battery threshold: 11.5V
                    if voltage < 11.5:
                        vehicle_update['bateriabaixa'] = True
                        vehicle_update['ultimoalertabateria'] = datetime.now()
                        
                        # Send notification
                        vehicle = await db_manager.get_vehicle_by_imei_async(imei)
                        placa = vehicle.get('dsplaca') if vehicle else None
                        notification_service.notify_low_battery(imei, voltage, placa)
                        
                        logger.warning(f"Low battery alert for IMEI {imei}: {voltage}V")
                    else:
                        vehicle_update['bateriabaixa'] = False
                
                await db_manager.upsert_vehicle_async(vehicle_update)
            else:
                logger.debug(f"BUFF message GTEPS for IMEI {imei} - only saved to vehicle_data")
            
        except Exception as e:
            logger.error(f"Error handling external power: {e}")
    
    async def _handle_power_on(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTPNA - Power On"""
        await self._save_location_data(parsed, raw_message)
    
    async def _handle_power_off(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTPFA - Power Off"""
        await self._save_location_data(parsed, raw_message)
    
    async def _handle_motion_start(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTMPN - Motion Start"""
        await self._save_location_data(parsed, raw_message)
    
    async def _handle_motion_stop(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTMPF - Motion Stop"""
        await self._save_location_data(parsed, raw_message)
    
    async def _handle_battery_start_charge(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTBTC - Battery Start Charging"""
        await self._save_location_data(parsed, raw_message)
    
    async def _handle_battery_stop_charge(self, parsed: Dict[str, Any], raw_message: str):
        """Handle GTSTC - Battery Stop Charging"""
        await self._save_location_data(parsed, raw_message)
    
    async def _handle_motion_state(self, parsed: Dict[str, Any]):
        """Handle GTSTT - Motion State Change"""
        try:
            imei = parsed.get('imei')
            if not imei:
                return
            
            vehicle_update = {
                'IMEI': imei,
                'tsusermanu': datetime.now()
            }
            
            await db_manager.upsert_vehicle_async(vehicle_update)
            
        except Exception as e:
            logger.error(f"Error handling motion state: {e}")
    
    async def _save_location_data(self, parsed: Dict[str, Any], raw_message: str):
        """Save location data for various message types"""
        try:
            imei = parsed.get('imei')
            if not imei:
                return
            
            # Check if it's a BUFF message (buffered/historical data)
            is_buff = parsed.get('category') == 'BUFF'
            
            # For BUFF messages, use device timestamp for both fields
            device_time = parsed.get('send_time')
            if is_buff and device_time:
                server_time = device_time
            else:
                server_time = datetime.now()
            
            vehicle_data = VehicleData(
                imei=imei,
                longitude=parsed.get('longitude'),
                latitude=parsed.get('latitude'),
                altitude=parsed.get('altitude'),
                timestamp=server_time,
                deviceTimestamp=device_time,
                mensagem_raw=raw_message
            )
            
            await db_manager.insert_vehicle_data_async(vehicle_data)
            
            # Only update Vehicle table if NOT a BUFF message
            if not is_buff:
                vehicle_update = {
                    'IMEI': imei,
                    'tsusermanu': datetime.now(),
                    'longitude': parsed.get('longitude'),
                    'latitude': parsed.get('latitude'),
                    'altitude': parsed.get('altitude')
                }
                
                await db_manager.upsert_vehicle_async(vehicle_update)
            else:
                logger.debug(f"BUFF message for IMEI {imei} - only saved to vehicle_data")
            
        except Exception as e:
            logger.error(f"Error saving location data: {e}")
    
    async def _check_pending_commands(self, imei: str) -> Optional[str]:
        """Check if there are pending commands for this device"""
        try:
            if not imei:
                return None
            
            # Get vehicle to check for pending commands
            vehicle = await db_manager.get_vehicle_by_imei_async(imei)
            
            if not vehicle:
                return None
            
            # Check for block/unblock command
            if vehicle.get('comandobloqueo') is not None:
                comando_bloquear = vehicle.get('comandobloqueo')
                
                # Generate GTOUT command
                # Format: AT+GTOUT=gv50,1,<output_status>,,,<password>$
                output_status = 1 if comando_bloquear else 0
                password = Config.DEFAULT_PASSWORD
                command = f"AT+GTOUT={password},1,{output_status},,,$"
                
                logger.info(f"Sending block command to IMEI {imei}: {'block' if comando_bloquear else 'unblock'}")
                return command
            
            # Check for IP change command
            if vehicle.get('comandotrocarip'):
                # Generate GTSRI command
                # Format: AT+GTSRI=gv50,3,2,220,178.87.210,10041,1,0.0.0.0,0,,,,,FFFF$
                password = Config.DEFAULT_PASSWORD
                server_ip = Config.PRIMARY_SERVER_IP
                server_port = Config.PRIMARY_SERVER_PORT
                backup_ip = Config.BACKUP_SERVER_IP
                backup_port = Config.BACKUP_SERVER_PORT
                
                command = (f"AT+GTSRI={password},3,2,220,{server_ip},{server_port},1,"
                          f"{backup_ip},{backup_port},,,,,FFFF$")
                
                # Clear command flag
                vehicle_update = {
                    'IMEI': imei,
                    'comandotrocarip': None
                }
                await db_manager.upsert_vehicle_async(vehicle_update)
                
                logger.info(f"Sending IP change command to IMEI {imei}")
                return command
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking pending commands: {e}")
            return None