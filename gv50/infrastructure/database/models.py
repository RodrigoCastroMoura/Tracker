from datetime import datetime
from mongoengine import (
    Document, StringField, BooleanField, FloatField,
    DateTimeField, ReferenceField, signals
)


class BaseDocument(Document):
    """Base document with audit fields"""
    meta = {'abstract': True}
    
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        document.updated_at = datetime.now()


class CustomerDocument(BaseDocument):
    """Customer MongoDB document - read-only customer data"""
    meta = {
        'collection': 'customers',
        'indexes': [
            {'fields': ['email'], 'unique': True, 'sparse': True},
            {'fields': ['document'], 'unique': True, 'sparse': True},
            {'fields': ['phone'], 'sparse': True}
        ]
    }
    
    name = StringField()
    email = StringField(unique=True, sparse=True)
    document = StringField(unique=True, sparse=True)
    phone = StringField()
    fcm_token = StringField()


class VehicleDocument(BaseDocument):
    """Vehicle MongoDB document"""
    meta = {
        'collection': 'vehicles',
        'indexes': [
            {'fields': ['IMEI'], 'unique': True},
            {'fields': ['dsplaca'], 'unique': True, 'sparse': True},
            {'fields': ['customer_id'], 'sparse': True}
        ]
    }
    
    IMEI = StringField(required=True, unique=True)
    dsplaca = StringField(unique=True, sparse=True)
    customer_id = ReferenceField('CustomerDocument', dbref=False)
    bloqueado = BooleanField(default=False)
    ignicao = BooleanField(default=False)
    comandobloqueo = BooleanField()
    bateriavoltagem = FloatField()
    bateriabaixa = BooleanField(default=False)
    ultimoalertabateria = DateTimeField()
    latitude = FloatField()
    longitude = FloatField()
    velocidade = FloatField()
    direcao = FloatField()
    altitude = FloatField()
    odometro = FloatField()
    horimetro = FloatField()
    ultimo_ip = StringField()
    ip_antigo = StringField()
    tsrastreador = DateTimeField()
    tsusermanu = DateTimeField()


signals.pre_save.connect(BaseDocument.pre_save, sender=CustomerDocument)
signals.pre_save.connect(BaseDocument.pre_save, sender=VehicleDocument)
