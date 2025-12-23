import asyncio
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from mongoengine import connect, disconnect
from bson import ObjectId
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import Config
from logger import logger
from models import VehicleData, Vehicle, Customer


class DatabaseManager:
    """Database manager for MongoDB operations with connection pooling"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.connect()
        self.setup_collections()
    
    def connect(self):
        """Connect to MongoDB with connection pooling"""
        try:
            self.client = MongoClient(
                Config.MONGODB_URI,
                maxPoolSize=200,
                minPoolSize=50,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[Config.DATABASE_NAME]
            self.client.admin.command('ping')
            
            connect(host=Config.MONGODB_URI, db=Config.DATABASE_NAME)
            
            logger.info(f"Connected to MongoDB database: {Config.DATABASE_NAME} (with connection pooling)")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def setup_collections(self):
        """Setup MongoDB collections and indexes"""
        try:
            collections_indexes = {
                'vehicle_data': [
                    ('imei', ASCENDING),
                    ('timestamp', ASCENDING)
                ],
                'vehicles': [
                    ('IMEI', ASCENDING),
                    ('tsusermanu', ASCENDING),
                    ('dsplaca', ASCENDING)
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
        """Insert vehicle tracking data (sync version)"""
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
    
    async def insert_vehicle_data_async(self, vehicle_data: VehicleData) -> bool:
        """Insert vehicle tracking data (async wrapper)"""
        return await asyncio.to_thread(self.insert_vehicle_data, vehicle_data)
    
    def upsert_vehicle(self, vehicle_data: Dict[str, Any]) -> bool:
        """Update or insert vehicle information using MongoEngine (sync version)"""
        try:
            imei = vehicle_data.get('IMEI')
            if not imei:
                logger.error("Cannot upsert vehicle without IMEI")
                return False
            
            filtered_data = {k: v for k, v in vehicle_data.items() 
                           if k not in ['created_by', 'updated_by', '_id']}
            
            date_fields = ['created_at', 'updated_at', 'ultimoalertabateria', 'tsusermanu']
            for field in date_fields:
                if field in filtered_data and isinstance(filtered_data[field], str):
                    try:
                        from dateutil import parser as date_parser
                        filtered_data[field] = date_parser.parse(filtered_data[field])
                    except Exception:
                        filtered_data.pop(field, None)
            
            existing_vehicle = Vehicle.objects(IMEI=imei).first()
            
            if existing_vehicle:
                for key, value in filtered_data.items():
                    if hasattr(existing_vehicle, key):
                        setattr(existing_vehicle, key, value)
                existing_vehicle.save()
            else:
                new_vehicle = Vehicle(**filtered_data)
                new_vehicle.save()
            
            return True
        except Exception as e:
            logger.error(f"Error upserting vehicle for IMEI {vehicle_data.get('IMEI')}: {e}")
            return False
    
    async def upsert_vehicle_async(self, vehicle_data: Dict[str, Any]) -> bool:
        """Update or insert vehicle information (async wrapper)"""
        return await asyncio.to_thread(self.upsert_vehicle, vehicle_data)
    
    def get_vehicle_by_imei(self, imei: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by IMEI using MongoEngine (sync version)"""
        try:
            vehicle = Vehicle.objects(IMEI=imei).first()
            if vehicle:
                result = vehicle.to_dict()
                if vehicle.customer_id:
                    result['customer_id'] = str(vehicle.customer_id.id)
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting vehicle for IMEI {imei}: {e}")
            return None
    
    async def get_vehicle_by_imei_async(self, imei: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by IMEI (async wrapper)"""
        return await asyncio.to_thread(self.get_vehicle_by_imei, imei)
    
    def get_customer_by_id(self, customer_id) -> Optional[Dict[str, Any]]:
        """Get customer information by ID"""
        try:
            if isinstance(customer_id, str):
                customer_id = ObjectId(customer_id)
            customer = Customer.objects(id=customer_id).first()
            if customer:
                return customer.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting customer for ID {customer_id}: {e}")
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
            disconnect()
            logger.info("Database connection closed")
    
    def close_connection(self):
        """Alias for close method"""
        self.close()
        
    def get_pending_commands(self, imei: str) -> List[Dict[str, Any]]:
        """Get pending commands for a vehicle"""
        try:
            if self.db is None:
                return []
            return []
        except Exception as e:
            logger.error(f"Error getting pending commands for IMEI {imei}: {e}")
            return []


db_manager = DatabaseManager()
