from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from mongoengine import Document, StringField, BooleanField, DateTimeField, IntField, FloatField

@dataclass
class VehicleData:
    """Vehicle tracking data model - apenas dados de localização"""
    imei: str
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    altitude: Optional[str] = None
    timestamp: Optional[datetime] = None  # Data do servidor
    deviceTimestamp: Optional[datetime] = None  # Data do dispositivo convertida para datetime
    mensagem_raw: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        return asdict(self)

class BaseDocument(Document):
    """Base document class with audit fields"""
    meta = {
        'abstract': True,
        'strict': False  # Ignore unknown fields in database (like old created_by/updated_by)
    }
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super(BaseDocument, self).save(*args, **kwargs)

    def to_dict(self):
        """Base method for consistent dictionary representation"""
        result = {
            'id': str(self.id) if hasattr(self, 'id') and self.id else None,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None,
        }
        return result

class Vehicle(BaseDocument):
    """Vehicle information model - estrutura conforme solicitado"""
    # Campo obrigatório
    IMEI = StringField(required=True, max_length=50)
    dsplaca = StringField(max_length=10)  # Placa do veículo
    dsmodelo = StringField(max_length=100)  # Modelo do veículo
    dsmarca = StringField(max_length=100)  # Marca do veículo
    ano = IntField()  # Ano do veículo
    comandobloqueo = BooleanField(default=None)  # True = bloquear, False = desbloquear, None = sem comando
    bloqueado = BooleanField(default=False)  # Status atual de bloqueio
    comandotrocarip = BooleanField(default=None)  # True = comando para trocar IP pendente
    ignicao = BooleanField(default=False)  # Status da ignição
    bateriavoltagem = FloatField()  # Voltagem atual da bateria
    bateriabaixa = BooleanField(default=False)  # True se bateria estiver baixa
    ultimoalertabateria = DateTimeField()  # Timestamp do último alerta
    status = StringField(choices=['active', 'inactive'], default='active')
    visible = BooleanField(default=True)  # Campo para exclusão lógica

    meta = {
        'collection': 'vehicles',
        'indexes': [
            # Use explicit names to avoid conflicts
            {'fields': ['IMEI'], 'unique': True, 'name': 'idx_vehicle_imei_unique'},
            {'fields': ['dsplaca'], 'unique': True, 'name': 'idx_vehicle_placa_unique', 'sparse': True},
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
