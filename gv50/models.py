from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from mongoengine import Document, StringField, BooleanField, DateTimeField, IntField, FloatField, ReferenceField

@dataclass
class VehicleData:
    """Vehicle tracking data model - apenas dados de localização"""
    imei: str
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    altitude: Optional[str] = None
    timestamp: Optional[datetime] = None
    deviceTimestamp: Optional[datetime] = None
    mensagem_raw: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        return asdict(self)


class BaseDocument(Document):
    """Base document class with audit fields"""
    meta = {
        'abstract': True,
        'strict': False
    }
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
        return super(BaseDocument, self).save(*args, **kwargs)

    def to_dict(self):
        """Base method for consistent dictionary representation"""
        result = {
            'id': str(self.id) if hasattr(self, 'id') and self.id else None,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None,
        }
        return result


class Customer(BaseDocument):
    """Customer model - dados do cliente (somente leitura)"""
    name = StringField(max_length=200)
    email = StringField(max_length=200)
    document = StringField(max_length=50)
    phone = StringField(max_length=50)
    fcm_token = StringField()

    meta = {
        'collection': 'customers',
        'indexes': [
            {'fields': ['email'], 'unique': True, 'name': 'idx_customer_email_unique', 'sparse': True},
            {'fields': ['document'], 'unique': True, 'name': 'idx_customer_document_unique', 'sparse': True},
            {'fields': ['phone'], 'name': 'idx_customer_phone', 'sparse': True}
        ]
    }

    def to_dict(self):
        """Convert to dictionary for API responses"""
        base_dict = super(Customer, self).to_dict()
        base_dict.update({
            'name': self.name,
            'email': self.email,
            'document': self.document,
            'phone': self.phone,
            'fcm_token': self.fcm_token
        })
        return base_dict
    
    def has_fcm_token(self) -> bool:
        """Check if customer has a valid FCM token"""
        return self.fcm_token is not None and len(self.fcm_token) > 0


class Vehicle(BaseDocument):
    """Vehicle information model - estrutura conforme solicitado"""
    IMEI = StringField(required=True, max_length=50)
    dsplaca = StringField(max_length=10)
    dsmodelo = StringField(max_length=100)
    dsmarca = StringField(max_length=100)
    ano = IntField()
    customer_id = ReferenceField('Customer', dbref=False)
    comandobloqueo = BooleanField(default=None)
    bloqueado = BooleanField(default=False)
    comandotrocarip = BooleanField(default=None)
    ignicao = BooleanField(default=False)
    bateriavoltagem = FloatField()
    bateriabaixa = BooleanField(default=False)
    ultimoalertabateria = DateTimeField()
    status = StringField(choices=['active', 'inactive'], default='active')
    visible = BooleanField(default=True)

    meta = {
        'collection': 'vehicles',
        'indexes': [
            {'fields': ['IMEI'], 'unique': True, 'name': 'idx_vehicle_imei_unique'},
            {'fields': ['dsplaca'], 'unique': True, 'name': 'idx_vehicle_placa_unique', 'sparse': True},
            {'fields': ['customer_id'], 'name': 'idx_vehicle_customer', 'sparse': True}
        ]
    }
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        base_dict = super(Vehicle, self).to_dict()
        base_dict.update({
            'IMEI': self.IMEI,
            'dsplaca': self.dsplaca,
            'dsmodelo': self.dsmodelo,
            'ano': self.ano,
            'dsmarca': self.dsmarca,
            'customer_id': str(self.customer_id.id) if self.customer_id else None,
            'comandobloqueo': self.comandobloqueo,
            'bloqueado': self.bloqueado,
            'comandotrocarip': self.comandotrocarip,
            'ignicao': self.ignicao,
            'bateriavoltagem': self.bateriavoltagem,
            'bateriabaixa': self.bateriabaixa,
            'ultimoalertabateria': self.ultimoalertabateria.isoformat() if hasattr(self, 'ultimoalertabateria') and self.ultimoalertabateria else None,
            'status': self.status,
            'visible': self.visible
        })
        return base_dict
