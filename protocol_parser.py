import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from logger import logger

class QueclinkProtocolParser:
    """Parser for Queclink @Track protocol messages"""
    
    def __init__(self):
        self.message_patterns = {
            'GTFRI': self._parse_gtfri,
            'GTIGN': self._parse_gtign,
            'GTIGF': self._parse_gtigf,
            'GTOUT': self._parse_gtout,
            'GTPFA': self._parse_gtpfa,
            'GTPNA': self._parse_gtpna,
            'GTMPN': self._parse_gtmpn,
            'GTMPF': self._parse_gtmpf,
            'GTSOS': self._parse_gtsos,
            'GTRTL': self._parse_gtrtl,
            'GTTOW': self._parse_gttow,
            'GTDIS': self._parse_gtdis,
            'GTIOB': self._parse_gtiob,
            'GTSPD': self._parse_gtspd,
            'GTGEO': self._parse_gtgeo,
        }
    
    def parse_message(self, raw_message: str) -> Dict[str, any]:
        """Parse incoming message from GV50 device"""
        try:
            # Clean the message
            message = raw_message.strip()
            
            # Extract message type and data
            if ':' not in message:
                return {'error': 'Invalid message format', 'raw_message': raw_message}
            
            parts = message.split(':', 1)
            message_type = parts[0].strip()
            message_data = parts[1].strip() if len(parts) > 1 else ''
            
            # Parse based on message type
            if message_type in ['+RESP', '+BUFF', '+ACK']:
                return self._parse_protocol_message(message_type, message_data, raw_message)
            else:
                return {'error': 'Unknown message type', 'raw_message': raw_message}
                
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def _parse_protocol_message(self, msg_type: str, data: str, raw_message: str) -> Dict[str, any]:
        """Parse protocol-specific message data"""
        try:
            if not data:
                return {'error': 'Empty message data', 'raw_message': raw_message}
            
            # Split data by comma
            fields = data.split(',')
            
            if len(fields) < 3:
                return {'error': 'Insufficient data fields', 'raw_message': raw_message}
            
            # Extract report type
            report_type = fields[0].strip()
            
            # Get parser function
            parser_func = self.message_patterns.get(report_type)
            
            if parser_func:
                parsed_data = parser_func(fields, raw_message)
                parsed_data.update({
                    'message_type': msg_type,
                    'report_type': report_type,
                    'raw_message': raw_message
                })
                return parsed_data
            else:
                # Generic parsing for unknown report types
                return self._parse_generic(fields, raw_message, msg_type, report_type)
                
        except Exception as e:
            logger.error(f"Error parsing protocol message: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def _parse_gtfri(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTFRI (Fixed Report Information) message"""
        try:
            if len(fields) < 20:
                return {'error': 'Insufficient GTFRI fields', 'raw_message': raw_message}
            
            return {
                'protocol_version': fields[1] if len(fields) > 1 else None,
                'imei': fields[2] if len(fields) > 2 else None,
                'device_name': fields[3] if len(fields) > 3 else None,
                'gps_accuracy': fields[4] if len(fields) > 4 else None,
                'speed': fields[5] if len(fields) > 5 else None,
                'course': fields[6] if len(fields) > 6 else None,
                'altitude': fields[7] if len(fields) > 7 else None,
                'longitude': fields[8] if len(fields) > 8 else None,
                'latitude': fields[9] if len(fields) > 9 else None,
                'device_timestamp': fields[10] if len(fields) > 10 else None,
                'mcc': fields[11] if len(fields) > 11 else None,
                'mnc': fields[12] if len(fields) > 12 else None,
                'lac': fields[13] if len(fields) > 13 else None,
                'cell_id': fields[14] if len(fields) > 14 else None,
                'reserved1': fields[15] if len(fields) > 15 else None,
                'reserved2': fields[16] if len(fields) > 16 else None,
                'reserved3': fields[17] if len(fields) > 17 else None,
                'mileage': fields[18] if len(fields) > 18 else None,
                'send_time': fields[19] if len(fields) > 19 else None,
                'count_number': fields[20] if len(fields) > 20 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing GTFRI: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def _parse_gtign(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTIGN (Ignition On) message"""
        try:
            if len(fields) < 15:
                return {'error': 'Insufficient GTIGN fields', 'raw_message': raw_message}
            
            return {
                'protocol_version': fields[1] if len(fields) > 1 else None,
                'imei': fields[2] if len(fields) > 2 else None,
                'device_name': fields[3] if len(fields) > 3 else None,
                'ignition': True,
                'gps_accuracy': fields[4] if len(fields) > 4 else None,
                'speed': fields[5] if len(fields) > 5 else None,
                'course': fields[6] if len(fields) > 6 else None,
                'altitude': fields[7] if len(fields) > 7 else None,
                'longitude': fields[8] if len(fields) > 8 else None,
                'latitude': fields[9] if len(fields) > 9 else None,
                'device_timestamp': fields[10] if len(fields) > 10 else None,
                'send_time': fields[11] if len(fields) > 11 else None,
                'count_number': fields[12] if len(fields) > 12 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing GTIGN: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def _parse_gtigf(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTIGF (Ignition Off) message"""
        try:
            if len(fields) < 15:
                return {'error': 'Insufficient GTIGF fields', 'raw_message': raw_message}
            
            return {
                'protocol_version': fields[1] if len(fields) > 1 else None,
                'imei': fields[2] if len(fields) > 2 else None,
                'device_name': fields[3] if len(fields) > 3 else None,
                'ignition': False,
                'gps_accuracy': fields[4] if len(fields) > 4 else None,
                'speed': fields[5] if len(fields) > 5 else None,
                'course': fields[6] if len(fields) > 6 else None,
                'altitude': fields[7] if len(fields) > 7 else None,
                'longitude': fields[8] if len(fields) > 8 else None,
                'latitude': fields[9] if len(fields) > 9 else None,
                'device_timestamp': fields[10] if len(fields) > 10 else None,
                'send_time': fields[11] if len(fields) > 11 else None,
                'count_number': fields[12] if len(fields) > 12 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing GTIGF: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def _parse_gtout(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTOUT (Output Control) acknowledgment"""
        try:
            if len(fields) < 8:
                return {'error': 'Insufficient GTOUT fields', 'raw_message': raw_message}
            
            return {
                'protocol_version': fields[1] if len(fields) > 1 else None,
                'imei': fields[2] if len(fields) > 2 else None,
                'device_name': fields[3] if len(fields) > 3 else None,
                'output_status': fields[4] if len(fields) > 4 else None,
                'send_time': fields[5] if len(fields) > 5 else None,
                'count_number': fields[6] if len(fields) > 6 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing GTOUT: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def _parse_gtpfa(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTPFA (Power Off Alert)"""
        return self._parse_generic_location(fields, raw_message, 'power_off_alert')
    
    def _parse_gtpna(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTPNA (Power On Alert)"""
        return self._parse_generic_location(fields, raw_message, 'power_on_alert')
    
    def _parse_gtmpn(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTMPN (Moving Alert)"""
        return self._parse_generic_location(fields, raw_message, 'moving_alert')
    
    def _parse_gtmpf(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTMPF (Stop Moving Alert)"""
        return self._parse_generic_location(fields, raw_message, 'stop_moving_alert')
    
    def _parse_gtsos(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTSOS (SOS Alert)"""
        return self._parse_generic_location(fields, raw_message, 'sos_alert')
    
    def _parse_gtrtl(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTRTL (Request Track Location)"""
        return self._parse_generic_location(fields, raw_message, 'track_location')
    
    def _parse_gttow(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTTOW (Towing Alert)"""
        return self._parse_generic_location(fields, raw_message, 'towing_alert')
    
    def _parse_gtdis(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTDIS (Disconnection Alert)"""
        return self._parse_generic_location(fields, raw_message, 'disconnection_alert')
    
    def _parse_gtiob(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTIOB (Input/Output Status)"""
        return self._parse_generic_location(fields, raw_message, 'io_status')
    
    def _parse_gtspd(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTSPD (Speed Alert)"""
        return self._parse_generic_location(fields, raw_message, 'speed_alert')
    
    def _parse_gtgeo(self, fields: List[str], raw_message: str) -> Dict[str, any]:
        """Parse GTGEO (Geo-fence Alert)"""
        return self._parse_generic_location(fields, raw_message, 'geofence_alert')
    
    def _parse_generic_location(self, fields: List[str], raw_message: str, event_type: str) -> Dict[str, any]:
        """Generic parser for location-based messages"""
        try:
            if len(fields) < 10:
                return {'error': f'Insufficient {event_type} fields', 'raw_message': raw_message}
            
            return {
                'event_type': event_type,
                'protocol_version': fields[1] if len(fields) > 1 else None,
                'imei': fields[2] if len(fields) > 2 else None,
                'device_name': fields[3] if len(fields) > 3 else None,
                'gps_accuracy': fields[4] if len(fields) > 4 else None,
                'speed': fields[5] if len(fields) > 5 else None,
                'course': fields[6] if len(fields) > 6 else None,
                'altitude': fields[7] if len(fields) > 7 else None,
                'longitude': fields[8] if len(fields) > 8 else None,
                'latitude': fields[9] if len(fields) > 9 else None,
                'device_timestamp': fields[10] if len(fields) > 10 else None,
                'send_time': fields[11] if len(fields) > 11 else None,
                'count_number': fields[12] if len(fields) > 12 else None,
            }
        except Exception as e:
            logger.error(f"Error parsing {event_type}: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def _parse_generic(self, fields: List[str], raw_message: str, msg_type: str, report_type: str) -> Dict[str, any]:
        """Generic parser for unknown message types"""
        try:
            data = {
                'message_type': msg_type,
                'report_type': report_type,
                'raw_message': raw_message,
                'imei': fields[2] if len(fields) > 2 else None,
                'fields': fields
            }
            
            # Try to extract common fields
            if len(fields) > 5:
                data.update({
                    'protocol_version': fields[1] if len(fields) > 1 else None,
                    'device_name': fields[3] if len(fields) > 3 else None,
                })
            
            return data
        except Exception as e:
            logger.error(f"Error in generic parsing: {e}")
            return {'error': str(e), 'raw_message': raw_message}
    
    def generate_acknowledgment(self, parsed_data: Dict[str, any]) -> Optional[str]:
        """Generate acknowledgment response for device"""
        try:
            if 'imei' not in parsed_data or not parsed_data['imei']:
                return None
            
            # Basic ACK format for @Track protocol
            protocol_version = parsed_data.get('protocol_version', '090200')
            imei = parsed_data['imei']
            device_name = parsed_data.get('device_name', '')
            count_number = parsed_data.get('count_number', '0001')
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Generate ACK based on message type
            report_type = parsed_data.get('report_type', 'GTFRI')
            
            ack_message = f"+ACK:{report_type},{protocol_version},{imei},{device_name},,{count_number},{timestamp},11F0$"
            
            return ack_message
            
        except Exception as e:
            logger.error(f"Error generating acknowledgment: {e}")
            return None

# Global protocol parser instance
protocol_parser = QueclinkProtocolParser()
