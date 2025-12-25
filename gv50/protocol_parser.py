#!/usr/bin/env python3
"""
Protocol Parser for GV50 GPS Tracker
Parses incoming messages according to GV50 @Track Air Interface Protocol
"""

from typing import Optional, Dict, Any
from datetime import datetime
from logger import logger
from datetime_converter import convert_device_timestamp


class ProtocolParser:
    """Parser for GV50 protocol messages"""
    
    def parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse GV50 protocol message
        
        Args:
            message: Raw message string
            
        Returns:
            Parsed message dictionary or None if parsing fails
        """
        try:
            message = message.strip()
            
            if not message:
                return None
            
            # GV50 messages start with '+' and end with '$'
            if not message.startswith('+') or not message.endswith('$'):
                logger.warning(f"Invalid message format: {message[:50]}")
                return None
            
            # Remove delimiters
            message = message[1:-1]  # Remove '+' and '$'
            
            # Split by comma
            parts = message.split(',')
            
            if len(parts) < 2:
                logger.warning(f"Insufficient parts in message: {message[:50]}")
                return None
            
            # Extract message type
            header = parts[0].split(':')
            if len(header) != 2:
                logger.warning(f"Invalid header format: {parts[0]}")
                return None
            
            msg_category = header[0]  # RESP, ACK, etc
            msg_type = header[1]  # GTFRI, GTHBD, etc
            
            # Parse based on message type
            if msg_type == 'GTFRI':
                return self._parse_gtfri(parts, msg_category)
            elif msg_type == 'GTHBD':
                return self._parse_gthbd(parts, msg_category)
            elif msg_type == 'GTIGN':
                return self._parse_gtign(parts, msg_category)
            elif msg_type == 'GTIGF':
                return self._parse_gtigf(parts, msg_category)
            elif msg_type == 'GTOUT':
                return self._parse_gtout(parts, msg_category)
            elif msg_type == 'GTEPS':
                return self._parse_gteps(parts, msg_category)
            elif msg_type == 'GTPNA':
                return self._parse_gtpna(parts, msg_category)
            elif msg_type == 'GTPFA':
                return self._parse_gtpfa(parts, msg_category)
            elif msg_type == 'GTMPN':
                return self._parse_gtmpn(parts, msg_category)
            elif msg_type == 'GTMPF':
                return self._parse_gtmpf(parts, msg_category)
            elif msg_type == 'GTBTC':
                return self._parse_gtbtc(parts, msg_category)
            elif msg_type == 'GTSTC':
                return self._parse_gtstc(parts, msg_category)
            elif msg_type == 'GTSTT':
                return self._parse_gtstt(parts, msg_category)
            elif msg_type in ['GTBSI', 'GTSRI', 'GTDOG', 'GTFFC']:
                # ACK messages
                return self._parse_ack(parts, msg_category, msg_type)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                return {'message_type': msg_type, 'raw_parts': parts}
                
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    def _parse_gtfri(self, parts: list, category: str) -> Dict[str, Any]:
        """
        Parse GTFRI - Fixed Report Information
        Format: +RESP:GTFRI,protocol,imei,device_name,report_id,report_type,
                number,gps_accuracy,speed,azimuth,altitude,longitude,latitude,
                send_time,mcc,mnc,lac,cell_id,reserved,mileage,hour_meter,
                adc1,battery_voltage,input_status,output_status,event_status,
                send_interval,info_count,info_type,count_number$
        """
        try:
            result = {
                'message_type': 'GTFRI',
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
                'report_id': parts[4] if len(parts) > 4 else None,
                'gps_accuracy': parts[6] if len(parts) > 6 else None,
                'speed': parts[7] if len(parts) > 7 else None,
                'azimuth': parts[8] if len(parts) > 8 else None,
                'altitude': parts[9] if len(parts) > 9 else None,
                'longitude': parts[10] if len(parts) > 10 else None,
                'latitude': parts[11] if len(parts) > 11 else None,
            }
            
            # Parse send time
            if len(parts) > 12 and parts[12]:
                result['send_time'] = convert_device_timestamp(parts[12])
            
            # Network info
            result['mcc'] = parts[13] if len(parts) > 13 else None
            result['mnc'] = parts[14] if len(parts) > 14 else None
            result['lac'] = parts[15] if len(parts) > 15 else None
            result['cell_id'] = parts[16] if len(parts) > 16 else None
            
            # Additional info
            # result['battery_voltage'] = parts[21] if len(parts) > 21 else None
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing GTFRI: {e}")
            return {'message_type': 'GTFRI', 'error': str(e)}
    
    def _parse_gthbd(self, parts: list, category: str) -> Dict[str, Any]:
        """
        Parse GTHBD - Heartbeat
        Format: +ACK:GTHBD,protocol,imei,device_name,count_number,send_time,count$
        """
        try:
            return {
                'message_type': 'GTHBD',
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing GTHBD: {e}")
            return {'message_type': 'GTHBD', 'error': str(e)}
    
    def _parse_gtign(self, parts: list, category: str) -> Dict[str, Any]:
        """
        Parse GTIGN - Ignition On
        Format: +RESP:GTIGN,protocol,imei,device_name,report_id,report_type,
                gps_accuracy,speed,azimuth,altitude,longitude,latitude,
                send_time,mcc,mnc,lac,cell_id,reserved,mileage,input_status,
                count_number$
        """
        try:
            result = {
                'message_type': 'GTIGN',
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
                'gps_accuracy': parts[5] if len(parts) > 5 else None,
                'speed': parts[6] if len(parts) > 6 else None,
                'azimuth': parts[7] if len(parts) > 7 else None,
                'altitude': parts[8] if len(parts) > 8 else None,
                'longitude': parts[9] if len(parts) > 9 else None,
                'latitude': parts[10] if len(parts) > 10 else None,
            }
            
            if len(parts) > 11 and parts[11]:
                result['send_time'] = convert_device_timestamp(parts[11])
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing GTIGN: {e}")
            return {'message_type': 'GTIGN', 'error': str(e)}
    
    def _parse_gtigf(self, parts: list, category: str) -> Dict[str, Any]:
        """
        Parse GTIGF - Ignition Off
        Same format as GTIGN
        """
        result = self._parse_gtign(parts, category)
        result['message_type'] = 'GTIGF'
        return result
    
    def _parse_gtout(self, parts: list, category: str) -> Dict[str, Any]:
        """
        Parse GTOUT - Digital Output Port Status
        Format: +RESP:GTOUT,protocol,imei,device_name,output_id,output_status,
                send_time,count_number$
        """
        try:
            return {
                'message_type': 'GTOUT',
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
                'output_id': parts[4] if len(parts) > 4 else None,
                'output_status': int(parts[5]) if len(parts) > 5 and parts[5] else None,
            }
        except Exception as e:
            logger.error(f"Error parsing GTOUT: {e}")
            return {'message_type': 'GTOUT', 'error': str(e)}
    
    def _parse_gteps(self, parts: list, category: str) -> Dict[str, Any]:
        """
        Parse GTEPS - External Power Supply
        Format: +RESP:GTEPS,protocol,imei,device_name,report_type,gps_accuracy,
                speed,azimuth,altitude,longitude,latitude,send_time,mcc,mnc,
                lac,cell_id,reserved,mileage,battery_voltage,count_number$
        """
        try:
            result = {
                'message_type': 'GTEPS',
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
                'gps_accuracy': parts[5] if len(parts) > 5 else None,
                'speed': parts[6] if len(parts) > 6 else None,
                'azimuth': parts[7] if len(parts) > 7 else None,
                'altitude': parts[8] if len(parts) > 8 else None,
                'longitude': parts[9] if len(parts) > 9 else None,
                'latitude': parts[10] if len(parts) > 10 else None,
                'battery_voltage': parts[17] if len(parts) > 17 else None,
            }
            
            if len(parts) > 11 and parts[11]:
                result['send_time'] = convert_device_timestamp(parts[11])
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing GTEPS: {e}")
            return {'message_type': 'GTEPS', 'error': str(e)}
    
    def _parse_gtpna(self, parts: list, category: str) -> Dict[str, Any]:
        """Parse GTPNA - Power On"""
        return self._parse_generic_location(parts, category, 'GTPNA')
    
    def _parse_gtpfa(self, parts: list, category: str) -> Dict[str, Any]:
        """Parse GTPFA - Power Off"""
        return self._parse_generic_location(parts, category, 'GTPFA')
    
    def _parse_gtmpn(self, parts: list, category: str) -> Dict[str, Any]:
        """Parse GTMPN - Motion Start"""
        return self._parse_generic_location(parts, category, 'GTMPN')
    
    def _parse_gtmpf(self, parts: list, category: str) -> Dict[str, Any]:
        """Parse GTMPF - Motion Stop"""
        return self._parse_generic_location(parts, category, 'GTMPF')
    
    def _parse_gtbtc(self, parts: list, category: str) -> Dict[str, Any]:
        """Parse GTBTC - Battery Start Charging"""
        return self._parse_generic_location(parts, category, 'GTBTC')
    
    def _parse_gtstc(self, parts: list, category: str) -> Dict[str, Any]:
        """Parse GTSTC - Battery Stop Charging"""
        return self._parse_generic_location(parts, category, 'GTSTC')
    
    def _parse_gtstt(self, parts: list, category: str) -> Dict[str, Any]:
        """
        Parse GTSTT - Motion State Change
        Format: +RESP:GTSTT,protocol,imei,device_name,state,send_time,count_number$
        """
        try:
            return {
                'message_type': 'GTSTT',
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
                'state': parts[4] if len(parts) > 4 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing GTSTT: {e}")
            return {'message_type': 'GTSTT', 'error': str(e)}
    
    def _parse_generic_location(self, parts: list, category: str, msg_type: str) -> Dict[str, Any]:
        """
        Parse generic location-based message
        Format similar to GTIGN
        """
        try:
            result = {
                'message_type': msg_type,
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
            }
            
            # Try to extract location if available
            if len(parts) > 10:
                result['longitude'] = parts[9] if len(parts) > 9 else None
                result['latitude'] = parts[10] if len(parts) > 10 else None
                result['altitude'] = parts[8] if len(parts) > 8 else None
                
                if len(parts) > 11 and parts[11]:
                    result['send_time'] = convert_device_timestamp(parts[11])
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing {msg_type}: {e}")
            return {'message_type': msg_type, 'error': str(e)}
    
    def _parse_ack(self, parts: list, category: str, msg_type: str) -> Dict[str, Any]:
        """
        Parse ACK messages
        Format: +ACK:GTXXX,protocol,imei,device_name,count_number,send_time,count$
        """
        try:
            return {
                'message_type': f'ACK_{msg_type}',
                'category': category,
                'protocol': parts[1] if len(parts) > 1 else None,
                'imei': parts[2] if len(parts) > 2 else None,
                'device_name': parts[3] if len(parts) > 3 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing ACK: {e}")
            return {'message_type': f'ACK_{msg_type}', 'error': str(e)}