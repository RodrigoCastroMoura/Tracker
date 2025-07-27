from typing import Dict, Optional
from database import db_manager
from models import VehicleData, Vehicle
from logger import logger
from datetime import datetime
from datetime_converter import convert_device_timestamp

class MessageHandler:
    """Simplified message handler - only save to vehicle_data and read from vehicles"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def process_message(self, parsed_data: Dict[str, str], raw_message: str):
        """Process parsed message - save data and update vehicle status"""
        try:
            imei = parsed_data.get('imei', '')
            report_type = parsed_data.get('report_type', '')
            
            # Save GPS tracking data to vehicle_data table
            if report_type in ['GTFRI', 'GTIGN', 'GTIGF', 'GTSTT', 'GTOUT', 'GTBTC', 'GTBPL']:
                await self._save_vehicle_data(parsed_data, raw_message)
            
            # Update vehicle ignition status only
            if report_type in ['GTIGN', 'GTIGF']:
                await self._update_vehicle_ignition(parsed_data)
                
        except Exception as e:
            logger.error(f"Error processing message for IMEI {imei}: {e}")
    
    async def _save_vehicle_data(self, parsed_data: Dict[str, str], raw_message: str):
        """Save GPS data to vehicle_data table"""
        try:
            # Extract coordinates
            longitude = parsed_data.get('longitude')
            latitude = parsed_data.get('latitude')
            altitude = parsed_data.get('altitude', '0')
            
            # Convert device timestamp
            device_timestamp_str = parsed_data.get('device_timestamp')
            device_timestamp = None
            if device_timestamp_str and device_timestamp_str != '0000':
                device_timestamp = convert_device_timestamp(device_timestamp_str)
            
            # Create vehicle data record
            vehicle_data = VehicleData(
                imei=parsed_data.get('imei', ''),
                longitude=float(longitude) if longitude else 0.0,
                latitude=float(latitude) if latitude else 0.0,
                altitude=float(altitude) if altitude else 0.0,
                timestamp=datetime.utcnow(),
                deviceTimestamp=device_timestamp,
                systemDate=datetime.utcnow(),
                mensagem_raw=raw_message
            )
            
            # Save to database
            self.db_manager.save_vehicle_data(vehicle_data)
            
        except Exception as e:
            logger.error(f"Error saving vehicle data: {e}")
    
    async def _update_vehicle_ignition(self, parsed_data: Dict[str, str]):
        """Update vehicle ignition status"""
        try:
            imei = parsed_data.get('imei', '')
            report_type = parsed_data.get('report_type', '')
            
            # Read vehicle from database
            vehicle = self.db_manager.get_vehicle_by_imei(imei)
            if vehicle:
                # Update ignition status
                vehicle_data = dict(vehicle)
                if '_id' in vehicle_data:
                    del vehicle_data['_id']
                
                if report_type == 'GTIGN':
                    vehicle_data['ignicao'] = True
                elif report_type == 'GTIGF':
                    vehicle_data['ignicao'] = False
                
                vehicle_data['tsusermanu'] = datetime.utcnow()
                
                # Save updated vehicle
                updated_vehicle = Vehicle(**vehicle_data)
                self.db_manager.upsert_vehicle(updated_vehicle)
                
        except Exception as e:
            logger.error(f"Error updating vehicle ignition: {e}")

# Global message handler instance
message_handler = MessageHandler()