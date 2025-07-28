from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import Config
from logger import logger
from models import VehicleData, Vehicle

class DatabaseManager:
    """Database manager for MongoDB operations - apenas duas tabelas"""
    
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
        """Setup MongoDB collections and indexes - apenas duas tabelas"""
        try:
            # Create indexes for better performance - apenas para as duas tabelas solicitadas
            collections_indexes = {
                'vehicle_data': [
                    ('imei', ASCENDING),
                    ('timestamp', ASCENDING)  # Removido ignition, agora só na vehicles
                ],
                'vehicles': [
                    ('IMEI', ASCENDING),  # Novo campo IMEI maiúsculo
                    ('tsusermanu', ASCENDING),  # Novo campo timestamp
                    ('dsplaca', ASCENDING)  # Novo campo placa
                ]
            }
            
            for collection_name, indexes in collections_indexes.items():
                collection = self.db[collection_name]
                for index in indexes:
                    collection.create_index([index])
            
            logger.info("Database collections and indexes setup completed - 2 tables: vehicle_data, vehicles")
        except Exception as e:
            logger.error(f"Error setting up collections: {e}")
    
    def insert_vehicle_data(self, vehicle_data: VehicleData) -> bool:
        """Insert vehicle tracking data"""
        try:
            if self.db is None:
                return False
            collection = self.db['vehicle_data']
            result = collection.insert_one(vehicle_data.to_dict())
            logger.debug(f"Inserted vehicle_data for IMEI: {vehicle_data.imei}")
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error inserting vehicle data for IMEI {vehicle_data.imei}: {e}")
            return False
    
    def upsert_vehicle(self, vehicle: Vehicle) -> bool:
        """Update or insert vehicle information - handles both imei and IMEI fields"""
        try:
            if self.db is None:
                return False
            collection = self.db['vehicles']
            
            # Try to find existing vehicle with either field name
            existing = collection.find_one({'imei': vehicle.IMEI})
            if not existing:
                existing = collection.find_one({'IMEI': vehicle.IMEI})
            
            update_data = vehicle.to_dict()
            
            if existing:
                # Update existing document using its _id
                result = collection.update_one(
                    {'_id': existing['_id']},
                    {'$set': update_data}
                )
                operation = 'UPDATE'
            else:
                # Insert new document
                result = collection.insert_one(update_data)
                operation = 'INSERT'
            
            logger.debug(f"{operation} vehicle for IMEI: {vehicle.IMEI}")
            return True
        except Exception as e:
            logger.error(f"Error upserting vehicle for IMEI {vehicle.IMEI}: {e}")
            return False
    
    def get_vehicle_by_imei(self, imei: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by IMEI - search both imei and IMEI fields"""
        try:
            if self.db is None:
                return None
            collection = self.db['vehicles']
            # Try both field names for compatibility
            vehicle = collection.find_one({'imei': imei})
            if not vehicle:
                vehicle = collection.find_one({'IMEI': imei})
            logger.debug(f"Retrieved vehicle for IMEI: {imei}")
            return vehicle
        except Exception as e:
            logger.error(f"Error getting vehicle for IMEI {imei}: {e}")
            return None
    
    def get_latest_vehicle_data(self, imei: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest vehicle tracking data by IMEI"""
        try:
            if self.db is None:
                return []
            collection = self.db['vehicle_data']
            data = list(collection.find({'imei': imei})
                       .sort('server_timestamp', -1)
                       .limit(limit))
            logger.log_database_operation('SELECT', 'vehicle_data', imei)
            return data
        except Exception as e:
            logger.error(f"Error getting vehicle data for IMEI {imei}: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    def close_connection(self):
        """Alias for close method"""
        self.close()
        
    def get_pending_commands(self, imei: str) -> List[Dict[str, Any]]:
        """Get pending commands for a vehicle - simplified version"""
        try:
            if self.db is None:
                return []
            # Para simplicidade, retornamos lista vazia - comandos podem ser implementados futuramente
            return []
        except Exception as e:
            logger.error(f"Error getting pending commands for IMEI {imei}: {e}")
            return []

# Global database manager instance
db_manager = DatabaseManager()