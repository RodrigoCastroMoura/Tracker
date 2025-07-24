import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from gv50.logger import logger

class QueclinkProtocolParser:
    """Parser for Queclink @Track protocol messages"""
    
    def __init__(self):
        # Basic message patterns for Queclink @Track protocol
        self.message_patterns = {
            'GTFRI': r'\+(?P<msg_type>RESP|BUFF|ACK):GTFRI,(?P<protocol_version>[^,]*),(?P<imei>[^,]*),(?P<device_name>[^,]*),(?P<reserved1>[^,]*),(?P<reserved2>[^,]*),(?P<gps_accuracy>[^,]*),(?P<speed>[^,]*),(?P<course>[^,]*),(?P<altitude>[^,]*),(?P<longitude>[^,]*),(?P<latitude>[^,]*),(?P<device_timestamp>[^,]*),(?P<mcc>[^,]*),(?P<mnc>[^,]*),(?P<lac>[^,]*),(?P<cell_id>[^,]*),(?P<reserved3>[^,]*),(?P<odometer>[^,]*),(?P<count>\d+)\$',
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
            
            # Use appropriate pattern
            pattern = self.message_patterns.get(message_type)
            if not pattern:
                return {'error': f'No pattern for message type: {message_type}'}
            
            match = re.match(pattern, message)
            if not match:
                logger.debug(f"Failed to match pattern for {message_type}: {message}")
                return {'error': f'Message format invalid for {message_type}'}
            
            # Extract data from the match
            data = match.groupdict()
            
            # Add message type to the data
            data['report_type'] = message_type
            
            # Convert coordinates to proper format
            if data.get('longitude') and data.get('latitude'):
                try:
                    data['longitude'] = str(float(data['longitude']))
                    data['latitude'] = str(float(data['latitude']))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid coordinates in message: {message}")
            
            # Handle ignition status based on message type
            if message_type == 'GTIGN':
                data['ignition'] = True
            elif message_type == 'GTIGF':
                data['ignition'] = False
            
            # Convert numeric fields
            for field in ['speed', 'course', 'altitude', 'gps_accuracy']:
                if data.get(field):
                    try:
                        data[field] = str(float(data[field]))
                    except (ValueError, TypeError):
                        data[field] = '0'
            
            logger.debug(f"Successfully parsed {message_type} message for IMEI: {data.get('imei', 'unknown')}")
            return data
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return {'error': f'Parse error: {str(e)}'}
    
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