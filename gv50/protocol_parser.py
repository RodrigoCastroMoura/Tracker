import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from logger import logger

class QueclinkProtocolParser:
    """Parser for Queclink @Track protocol messages"""
    
    def __init__(self):
        # Basic message patterns for Queclink @Track protocol - flexible patterns
        self.message_patterns = {
            'GTFRI': r'\+(?P<msg_type>RESP|BUFF|ACK):GTFRI,(?P<protocol_version>[^,]*),(?P<imei>[^,]*),(?P<device_name>[^,]*),(?P<reserved1>[^,]*),(?P<gps_accuracy>[^,]*),(?P<speed>[^,]*),(?P<course>[^,]*),(?P<altitude>[^,]*),(?P<longitude>[^,]*),(?P<latitude>[^,]*),(?P<device_timestamp>[^,]*),(?P<mcc>[^,]*),(?P<mnc>[^,]*),(?P<lac>[^,]*),(?P<cell_id>[^,]*),(?P<reserved2>[^,]*),(?P<odometer>[^,]*),(?P<count>[^$]*)\$',
            'GTIGN': r'\+(?P<msg_type>RESP|BUFF|ACK):GTIGN,(?P<protocol_version>[^,]*),(?P<imei>[^,]*),(?P<device_name>[^,]*),(?P<report_id>[^,]*),(?P<report_type>[^,]*),(?P<reserved1>[^,]*),(?P<gps_accuracy>[^,]*),(?P<speed>[^,]*),(?P<course>[^,]*),(?P<altitude>[^,]*),(?P<longitude>[^,]*),(?P<latitude>[^,]*),(?P<device_timestamp>[^,]*),(?P<mcc>[^,]*),(?P<mnc>[^,]*),(?P<lac>[^,]*),(?P<cell_id>[^,]*),(?P<reserved2>[^,]*),(?P<odometer>[^,]*),(?P<count>\d+)\$',
            'GTIGF': r'\+(?P<msg_type>RESP|BUFF|ACK):GTIGF,(?P<protocol_version>[^,]*),(?P<imei>[^,]*),(?P<device_name>[^,]*),(?P<report_id>[^,]*),(?P<report_type>[^,]*),(?P<reserved1>[^,]*),(?P<gps_accuracy>[^,]*),(?P<speed>[^,]*),(?P<course>[^,]*),(?P<altitude>[^,]*),(?P<longitude>[^,]*),(?P<latitude>[^,]*),(?P<device_timestamp>[^,]*),(?P<mcc>[^,]*),(?P<mnc>[^,]*),(?P<lac>[^,]*),(?P<cell_id>[^,]*),(?P<reserved2>[^,]*),(?P<odometer>[^,]*),(?P<count>\d+)\$',
            'GTOUT': r'\+(?P<msg_type>RESP|BUFF|ACK):GTOUT,(?P<protocol_version>[^,]*),(?P<imei>[^,]*),(?P<device_name>[^,]*),(?P<report_id>[^,]*),(?P<report_type>[^,]*),(?P<reserved1>[^,]*),(?P<gps_accuracy>[^,]*),(?P<speed>[^,]*),(?P<course>[^,]*),(?P<altitude>[^,]*),(?P<longitude>[^,]*),(?P<latitude>[^,]*),(?P<device_timestamp>[^,]*),(?P<mcc>[^,]*),(?P<mnc>[^,]*),(?P<lac>[^,]*),(?P<cell_id>[^,]*),(?P<reserved2>[^,]*),(?P<odometer>[^,]*),(?P<count>\d+)\$'
        }
    
    def parse_message(self, message: str) -> Dict[str, str]:
        """Parse Queclink @Track protocol message"""
        try:
            message = message.strip()
            if not message:
                return {'error': 'Empty message'}
            
            # Determine message type from the message content
            message_type = self._detect_message_type(message)
            if not message_type:
                return {'error': 'Unknown message type'}
            
            # Parse GTFRI with flexible field-based approach
            if message_type == 'GTFRI':
                return self._parse_gtfri(message)
            
            # Use regex patterns for other message types
            pattern = self.message_patterns.get(message_type)
            if not pattern:
                return {'error': f'No pattern for message type: {message_type}'}
            
            match = re.match(pattern, message)
            if not match:
                logger.debug(f"Failed to match pattern for {message_type}: {message}")
                return {'error': f'Message format invalid for {message_type}'}
            
            # Extract data from the match
            data = match.groupdict()
            data['report_type'] = message_type
            
            # Handle ignition status based on message type
            if message_type == 'GTIGN':
                data['ignition'] = True
            elif message_type == 'GTIGF':
                data['ignition'] = False
            
            # Convert numeric fields
            self._convert_numeric_fields(data)
            
            logger.debug(f"Successfully parsed {message_type} message for IMEI: {data.get('imei', 'unknown')}")
            return data
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return {'error': f'Parse error: {str(e)}'}
    
    def _parse_gtfri(self, message: str) -> Dict[str, str]:
        """Parse GTFRI message based on C# implementation"""
        try:
            # Remove prefix and suffix
            if not message.startswith('+') or not message.endswith('$'):
                return {'error': 'Invalid message format'}
            
            # Split by ':' first to get msg_type and data part
            msg_parts = message[1:-1].split(':', 1)  # Remove + and $
            if len(msg_parts) != 2:
                return {'error': 'Invalid message structure'}
            
            msg_type = msg_parts[0]  # RESP, BUFF, ACK
            data_part = msg_parts[1]
            
            # Split data part by comma
            fields = data_part.split(',')
            
            if len(fields) < 14:  # Minimum required fields based on C# code
                return {'error': f'Insufficient fields in GTFRI: {len(fields)}'}
            
            # Map fields according to C# implementation:
            # C# GTFRI: comando[2]=IMEI, comando[8]=speed, comando[10]=altitude, comando[11]=longitude, comando[12]=latitude, comando[13]=dataDevice
            data = {
                'msg_type': msg_type,
                'report_type': 'GTFRI',
                'protocol_version': fields[1] if len(fields) > 1 else '',
                'imei': fields[2] if len(fields) > 2 else '',  # comando[2] no C#
                'device_name': fields[3] if len(fields) > 3 else '',
                'reserved1': fields[4] if len(fields) > 4 else '',
                'gps_accuracy': fields[5] if len(fields) > 5 else '0',
                'speed': fields[8] if len(fields) > 8 else '0',  # comando[8] no C# para GTFRI
                'course': fields[7] if len(fields) > 7 else '0',
                'altitude': fields[10] if len(fields) > 10 else '0',  # comando[10] no C#
                'longitude': fields[11] if len(fields) > 11 else '0',  # comando[11] no C#
                'latitude': fields[12] if len(fields) > 12 else '0',   # comando[12] no C#
                'device_timestamp': fields[13] if len(fields) > 13 else '',  # comando[13] no C#
                'mcc': fields[14] if len(fields) > 14 else '',
                'mnc': fields[15] if len(fields) > 15 else '',
                'lac': fields[16] if len(fields) > 16 else '',
                'cell_id': fields[17] if len(fields) > 17 else '',
                'reserved2': fields[18] if len(fields) > 18 else '',
                'odometer': fields[19] if len(fields) > 19 else '0',
                'count': fields[20] if len(fields) > 20 else '0'
            }
            
            # Convert numeric fields
            self._convert_numeric_fields(data)
            
            logger.debug(f"Successfully parsed GTFRI message for IMEI: {data.get('imei', 'unknown')}")
            return data
            
        except Exception as e:
            logger.error(f"Error parsing GTFRI: {e}")
            return {'error': f'GTFRI parse error: {str(e)}'}
    
    def _convert_numeric_fields(self, data: Dict[str, str]):
        """Convert numeric fields to proper format"""
        # Convert coordinates to proper format
        if data.get('longitude') and data.get('latitude'):
            try:
                data['longitude'] = str(float(data['longitude']))
                data['latitude'] = str(float(data['latitude']))
            except (ValueError, TypeError):
                logger.warning(f"Invalid coordinates: {data.get('longitude')}, {data.get('latitude')}")
        
        # Convert other numeric fields
        for field in ['speed', 'course', 'altitude', 'gps_accuracy']:
            if data.get(field):
                try:
                    data[field] = str(float(data[field]))
                except (ValueError, TypeError):
                    data[field] = '0'
    
    def _detect_message_type(self, message: str) -> Optional[str]:
        """Detect message type from the message content"""
        for msg_type in self.message_patterns.keys():
            if f':{msg_type},' in message:
                return msg_type
        return None
    
    def generate_acknowledgment(self, parsed_data: Dict[str, str]) -> Optional[str]:
        """Generate acknowledgment response for the device"""
        try:
            report_type = parsed_data.get('report_type', '')
            protocol_version = parsed_data.get('protocol_version', 'A10100')
            imei = parsed_data.get('imei', '')
            count = parsed_data.get('count', '0123')
            
            if not report_type or not imei:
                return None
            
            # Generate timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            
            # Generate simple checksum (simplified for this implementation)
            checksum = "11F0"
            
            # Build acknowledgment message
            ack_message = f"+ACK:{report_type},{protocol_version},{imei},,{count}$,{timestamp},{checksum}$"
            
            return ack_message
            
        except Exception as e:
            logger.error(f"Error generating acknowledgment: {e}")
            return None
    
    def parse_coordinates(self, longitude: str, latitude: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse and validate GPS coordinates"""
        try:
            lon = float(longitude) if longitude else None
            lat = float(latitude) if latitude else None
            
            # Basic validation
            if lon is not None and (lon < -180 or lon > 180):
                lon = None
            if lat is not None and (lat < -90 or lat > 90):
                lat = None
                
            return lon, lat
        except (ValueError, TypeError):
            return None, None

# Global protocol parser instance
protocol_parser = QueclinkProtocolParser()