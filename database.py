from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import Config
from logger import logger
from models import VehicleData, Vehicle, EventLog, MessageLog, IPChangeLog, VehicleCommands, BatteryEvent

class DatabaseManager:
    """Database manager for MongoDB operations"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.connect()
        self.setup_collections()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.DATABASE_NAME]
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {Config.DATABASE_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def setup_collections(self):
        """Setup MongoDB collections and indexes"""
        try:
            # Create indexes for better performance
            collections_indexes = {
                'vehicle_data': [
                    ('imei', ASCENDING),
                    ('server_timestamp', ASCENDING),
                    ('device_timestamp', ASCENDING)
                ],
                'vehicles': [
                    ('imei', ASCENDING),
                    ('last_update', ASCENDING)
                ],
                'event_logs': [
                    ('imei', ASCENDING),
                    ('event_type', ASCENDING),
                    ('timestamp', ASCENDING)
                ],
                'message_logs': [
                    ('imei', ASCENDING),
                    ('timestamp', ASCENDING),
                    ('message_direction', ASCENDING)
                ],
                'ip_change_logs': [
                    ('imei', ASCENDING),
                    ('timestamp', ASCENDING)
                ],
                'vehicle_commands': [
                    ('imei', ASCENDING),
                    ('plate_number', ASCENDING),
                    ('owner_cpf', ASCENDING)
                ],
                'battery_events': [
                    ('imei', ASCENDING),
                    ('timestamp', ASCENDING),
                    ('battery_level', ASCENDING)
                ]
            }
            
            for collection_name, indexes in collections_indexes.items():
                collection = self.db[collection_name]
                for index in indexes:
                    collection.create_index([index])
            
            logger.info("Database collections and indexes setup completed")
        except Exception as e:
            logger.error(f"Error setting up collections: {e}")
    
    def insert_vehicle_data(self, vehicle_data: VehicleData) -> bool:
        """Insert vehicle tracking data"""
        try:
            collection = self.db['vehicle_data']
            result = collection.insert_one(vehicle_data.to_dict())
            logger.log_database_operation('INSERT', 'vehicle_data', vehicle_data.imei)
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error inserting vehicle data for IMEI {vehicle_data.imei}: {e}")
            return False
    
    def upsert_vehicle(self, vehicle: Vehicle) -> bool:
        """Update or insert vehicle information"""
        try:
            collection = self.db['vehicles']
            filter_query = {'imei': vehicle.imei}
            update_data = vehicle.to_dict()
            
            result = collection.update_one(
                filter_query,
                {'$set': update_data},
                upsert=True
            )
            
            operation = 'UPDATE' if result.matched_count > 0 else 'INSERT'
            logger.log_database_operation(operation, 'vehicles', vehicle.imei)
            return True
        except Exception as e:
            logger.error(f"Error upserting vehicle for IMEI {vehicle.imei}: {e}")
            return False
    
    def get_vehicle_by_imei(self, imei: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by IMEI"""
        try:
            collection = self.db['vehicles']
            vehicle = collection.find_one({'imei': imei})
            logger.log_database_operation('SELECT', 'vehicles', imei)
            return vehicle
        except Exception as e:
            logger.error(f"Error getting vehicle for IMEI {imei}: {e}")
            return None
    
    def insert_event_log(self, event_log: EventLog) -> bool:
        """Insert event log"""
        try:
            collection = self.db['event_logs']
            result = collection.insert_one(event_log.to_dict())
            logger.log_database_operation('INSERT', 'event_logs', event_log.imei)
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error inserting event log for IMEI {event_log.imei}: {e}")
            return False
    
    def insert_message_log(self, message_log: MessageLog) -> bool:
        """Insert message log"""
        try:
            if not Config.SAVE_RAW_MESSAGES:
                return True
                
            collection = self.db['message_logs']
            result = collection.insert_one(message_log.to_dict())
            logger.log_database_operation('INSERT', 'message_logs', message_log.imei)
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error inserting message log for IMEI {message_log.imei}: {e}")
            return False
    
    def insert_ip_change_log(self, ip_log: IPChangeLog) -> bool:
        """Insert IP change log"""
        try:
            collection = self.db['ip_change_logs']
            result = collection.insert_one(ip_log.to_dict())
            logger.log_database_operation('INSERT', 'ip_change_logs', ip_log.imei)
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error inserting IP change log for IMEI {ip_log.imei}: {e}")
            return False

    def get_vehicle_commands_by_imei(self, imei: str) -> Optional[Dict[str, Any]]:
        """Get vehicle commands information by IMEI (para pesquisa apenas)"""
        try:
            collection = self.db['vehicle_commands']
            vehicle_cmd = collection.find_one({'imei': imei})
            logger.log_database_operation('SELECT', 'vehicle_commands', imei)
            return vehicle_cmd
        except Exception as e:
            logger.error(f"Error getting vehicle commands for IMEI {imei}: {e}")
            return None

    def get_vehicle_commands_by_plate(self, plate_number: str) -> Optional[Dict[str, Any]]:
        """Get vehicle commands information by plate number"""
        try:
            collection = self.db['vehicle_commands']
            vehicle_cmd = collection.find_one({'plate_number': plate_number})
            logger.log_database_operation('SELECT', 'vehicle_commands', plate_number)
            return vehicle_cmd
        except Exception as e:
            logger.error(f"Error getting vehicle commands for plate {plate_number}: {e}")
            return None

    def get_vehicle_commands_by_cpf(self, owner_cpf: str) -> List[Dict[str, Any]]:
        """Get all vehicles for an owner by CPF"""
        try:
            collection = self.db['vehicle_commands']
            vehicles = list(collection.find({'owner_cpf': owner_cpf}))
            logger.log_database_operation('SELECT', 'vehicle_commands', owner_cpf)
            return vehicles
        except Exception as e:
            logger.error(f"Error getting vehicles for CPF {owner_cpf}: {e}")
            return []

    def insert_battery_event(self, battery_event: BatteryEvent) -> bool:
        """Insert battery event"""
        try:
            collection = self.db['battery_events']
            result = collection.insert_one(battery_event.to_dict())
            logger.log_database_operation('INSERT', 'battery_events', battery_event.imei)
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error inserting battery event for IMEI {battery_event.imei}: {e}")
            return False
    
    def get_pending_commands(self, imei: str) -> List[Dict[str, Any]]:
        """Get pending commands for a vehicle"""
        try:
            collection = self.db['vehicles']
            vehicle = collection.find_one({'imei': imei})
            
            if not vehicle:
                return []
            
            commands = []
            
            # Check for block/unblock commands
            if vehicle.get('block_command_pending', False):
                command_type = 'block' if not vehicle.get('is_blocked', False) else 'unblock'
                commands.append({
                    'type': command_type,
                    'command': f'AT+GTOUT={Config.DEFAULT_PASSWORD},1,0,0,,,1234$' if command_type == 'block' else f'AT+GTOUT={Config.DEFAULT_PASSWORD},1,1,0,,,1234$'
                })
            
            return commands
        except Exception as e:
            logger.error(f"Error getting pending commands for IMEI {imei}: {e}")
            return []
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()
