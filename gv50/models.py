from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

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

@dataclass
class Vehicle:
    """Vehicle information model - estrutura conforme solicitado"""
    IMEI: str  # Campo obrigatório primeiro
    id: Optional[str] = None
    comandobloqueo: Optional[bool] = None  # True = bloquear, False = desbloquear, None = sem comando
    bloqueado: Optional[bool] = False  # Status atual de bloqueio
    comandotrocarip: Optional[bool] = None  # True = comando para trocar IP pendente
    ignicao: bool = False  # Status da ignição
    tsusermanu: Optional[datetime] = None  # Última atualização manual

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB operations"""
        data = asdict(self)
        now = datetime.utcnow()
        if self.tsusermanu is None:
            data['tsusermanu'] = now
        return data