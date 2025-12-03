from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from mongoengine import connect, disconnect
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import Config
from logger import logger
from models import VehicleData, Vehicle, Customer

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
            # Connect PyMongo for VehicleData operations
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.DATABASE_NAME]
            # Test connection
            self.client.admin.command('ping')
            
            # Connect MongoEngine for Vehicle model
            connect(host=Config.MONGODB_URI, db=Config.DATABASE_NAME)
            
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
    
    def upsert_vehicle(self, vehicle_data: Dict[str, Any]) -> bool:
        """Update or insert vehicle information using MongoEngine"""
        try:
            imei = vehicle_data.get('IMEI')
            if not imei:
                logger.error("Cannot upsert vehicle without IMEI")
                return False
            
            # Filter out incompatible fields from old database schema
            filtered_data = {k: v for k, v in vehicle_data.items() 
                           if k not in ['created_by', 'updated_by', '_id']}
            
            # Convert date strings to datetime objects for DateTimeFields
            date_fields = ['created_at', 'updated_at', 'ultimoalertabateria', 'tsusermanu']
            for field in date_fields:
                if field in filtered_data and isinstance(filtered_data[field], str):
                    try:
                        from dateutil import parser as date_parser
                        filtered_data[field] = date_parser.parse(filtered_data[field])
                    except:
                        # If parsing fails, remove the field
                        filtered_data.pop(field, None)
            
            # Try to get existing vehicle
            existing_vehicle = Vehicle.objects(IMEI=imei).first()
            
            if existing_vehicle:
                # Update existing vehicle
                for key, value in filtered_data.items():
                    if hasattr(existing_vehicle, key):
                        setattr(existing_vehicle, key, value)
                existing_vehicle.save()
            else:
                # Create new vehicle
                new_vehicle = Vehicle(**filtered_data)
                new_vehicle.save()
            
            return True
        except Exception as e:
            logger.error(f"Error upserting vehicle for IMEI {imei}: {e}")
            return False
    
    def get_vehicle_by_imei(self, imei: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by IMEI using MongoEngine"""
        try:
            vehicle = Vehicle.objects(IMEI=imei).first()
            if vehicle:
                return vehicle.to_dict()
            return None
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
            disconnect()  # Disconnect MongoEngine
            logger.info("Database connection closed")
    
    def close_connection(self):
        """Alias for close method"""
        self.close()
        
    def get_pending_commands(self, imei: str) -> List[Dict[str, Any]]:
        """Get pending commands for a vehicle - simplified version"""
        try:
            if self.db is None:
                return []
            return []
        except Exception as e:
            logger.error(f"Error getting pending commands for IMEI {imei}: {e}")
            return []
    
    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID"""
        try:
            from bson import ObjectId
            customer = Customer.objects(id=ObjectId(customer_id)).first()
            if customer:
                return customer.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting customer by ID {customer_id}: {e}")
            return None
    
    def get_customer_for_vehicle(self, imei: str) -> Optional[Dict[str, Any]]:
        """Get the customer associated with a vehicle by IMEI"""
        try:
            vehicle = Vehicle.objects(IMEI=imei).first()
            if vehicle and vehicle.customer_id:
                return vehicle.customer_id.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting customer for vehicle IMEI {imei}: {e}")
            return None


db_manager = DatabaseManager()