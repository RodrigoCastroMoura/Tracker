from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from ...domain.entities.customer import Customer
from ...domain.entities.vehicle import Vehicle
from ...domain.interfaces.repositories import CustomerRepository, VehicleRepository
from .models import CustomerDocument, VehicleDocument


class MongoCustomerRepository(CustomerRepository):
    """MongoDB implementation of CustomerRepository"""
    
    def _document_to_entity(self, doc: CustomerDocument) -> Customer:
        """Convert MongoDB document to domain entity"""
        if doc is None:
            return None
        return Customer(
            id=str(doc.id),
            name=doc.name,
            email=doc.email,
            document=doc.document,
            phone=doc.phone,
            fcm_token=doc.fcm_token,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            doc = CustomerDocument.objects(id=ObjectId(customer_id)).first()
            return self._document_to_entity(doc)
        except Exception:
            return None
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        doc = CustomerDocument.objects(email=email).first()
        return self._document_to_entity(doc)
    
    def get_by_document(self, document: str) -> Optional[Customer]:
        """Get customer by document"""
        doc = CustomerDocument.objects(document=document).first()
        return self._document_to_entity(doc)


class MongoVehicleRepository(VehicleRepository):
    """MongoDB implementation of VehicleRepository"""
    
    def __init__(self, db):
        """Initialize with database connection for PyMongo operations"""
        self.db = db
        self.collection = db['vehicles']
    
    def _document_to_entity(self, doc) -> Vehicle:
        """Convert MongoDB document to domain entity"""
        if doc is None:
            return None
        
        if isinstance(doc, dict):
            return Vehicle(
                id=str(doc.get('_id', '')),
                imei=doc.get('IMEI'),
                dsplaca=doc.get('dsplaca'),
                customer_id=str(doc.get('customer_id')) if doc.get('customer_id') else None,
                bloqueado=doc.get('bloqueado', False),
                ignicao=doc.get('ignicao', False),
                comandobloqueo=doc.get('comandobloqueo'),
                bateriavoltagem=doc.get('bateriavoltagem'),
                bateriabaixa=doc.get('bateriabaixa', False),
                ultimoalertabateria=doc.get('ultimoalertabateria'),
                latitude=doc.get('latitude'),
                longitude=doc.get('longitude'),
                velocidade=doc.get('velocidade'),
                direcao=doc.get('direcao'),
                altitude=doc.get('altitude'),
                odometro=doc.get('odometro'),
                horimetro=doc.get('horimetro'),
                ultimo_ip=doc.get('ultimo_ip'),
                ip_antigo=doc.get('ip_antigo'),
                tsrastreador=doc.get('tsrastreador'),
                tsusermanu=doc.get('tsusermanu'),
                created_at=doc.get('created_at'),
                updated_at=doc.get('updated_at')
            )
        
        return Vehicle(
            id=str(doc.id),
            imei=doc.IMEI,
            dsplaca=doc.dsplaca,
            customer_id=str(doc.customer_id.id) if doc.customer_id else None,
            bloqueado=doc.bloqueado,
            ignicao=doc.ignicao,
            comandobloqueo=doc.comandobloqueo,
            bateriavoltagem=doc.bateriavoltagem,
            bateriabaixa=doc.bateriabaixa,
            ultimoalertabateria=doc.ultimoalertabateria,
            latitude=doc.latitude,
            longitude=doc.longitude,
            velocidade=doc.velocidade,
            direcao=doc.direcao,
            altitude=doc.altitude,
            odometro=doc.odometro,
            horimetro=doc.horimetro,
            ultimo_ip=doc.ultimo_ip,
            ip_antigo=doc.ip_antigo,
            tsrastreador=doc.tsrastreador,
            tsusermanu=doc.tsusermanu,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
    
    def get_by_imei(self, imei: str) -> Optional[Vehicle]:
        """Get vehicle by IMEI"""
        doc = self.collection.find_one({'IMEI': imei})
        return self._document_to_entity(doc)
    
    def get_by_plate(self, plate: str) -> Optional[Vehicle]:
        """Get vehicle by plate (dsplaca)"""
        doc = self.collection.find_one({'dsplaca': plate})
        return self._document_to_entity(doc)
    
    def get_by_customer_id(self, customer_id: str) -> List[Vehicle]:
        """Get all vehicles for a customer"""
        try:
            docs = self.collection.find({'customer_id': ObjectId(customer_id)})
            return [self._document_to_entity(doc) for doc in docs]
        except Exception:
            return []
    
    def save(self, vehicle: Vehicle) -> Vehicle:
        """Save or update vehicle"""
        data = {
            'IMEI': vehicle.imei,
            'dsplaca': vehicle.dsplaca,
            'bloqueado': vehicle.bloqueado,
            'ignicao': vehicle.ignicao,
            'comandobloqueo': vehicle.comandobloqueo,
            'bateriavoltagem': vehicle.bateriavoltagem,
            'bateriabaixa': vehicle.bateriabaixa,
            'ultimoalertabateria': vehicle.ultimoalertabateria,
            'latitude': vehicle.latitude,
            'longitude': vehicle.longitude,
            'velocidade': vehicle.velocidade,
            'direcao': vehicle.direcao,
            'altitude': vehicle.altitude,
            'odometro': vehicle.odometro,
            'horimetro': vehicle.horimetro,
            'ultimo_ip': vehicle.ultimo_ip,
            'ip_antigo': vehicle.ip_antigo,
            'tsrastreador': vehicle.tsrastreador,
            'tsusermanu': vehicle.tsusermanu,
            'updated_at': datetime.now()
        }
        
        if vehicle.customer_id:
            try:
                data['customer_id'] = ObjectId(vehicle.customer_id)
            except Exception:
                pass
        
        data = {k: v for k, v in data.items() if v is not None}
        
        self.collection.update_one(
            {'IMEI': vehicle.imei},
            {'$set': data, '$setOnInsert': {'created_at': datetime.now()}},
            upsert=True
        )
        
        return self.get_by_imei(vehicle.imei)
    
    def upsert(self, vehicle_data: Dict[str, Any]) -> bool:
        """Upsert vehicle data by IMEI"""
        imei = vehicle_data.get('IMEI')
        if not imei:
            return False
        
        vehicle_data['updated_at'] = datetime.now()
        
        self.collection.update_one(
            {'IMEI': imei},
            {'$set': vehicle_data, '$setOnInsert': {'created_at': datetime.now()}},
            upsert=True
        )
        return True
    
    def get_customer_for_vehicle(self, imei: str) -> Optional[Customer]:
        """Get the customer associated with a vehicle"""
        vehicle = self.get_by_imei(imei)
        if vehicle and vehicle.customer_id:
            customer_repo = MongoCustomerRepository()
            return customer_repo.get_by_id(vehicle.customer_id)
        return None
