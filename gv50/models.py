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
    deviceTimestamp: str = ""  # Data do dispositivo apenas para referência
    deviceDateConverted: Optional[datetime] = None  # Data do dispositivo convertida
    mensagem_raw: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        return asdict(self)

@dataclass
class Vehicle:
    """Vehicle information model - estrutura conforme solicitado"""
    IMEI: str  # Campo obrigatório primeiro
    id: Optional[str] = None
    dsplaca: Optional[str] = None  # Placa do veículo
    dsmodelo: Optional[str] = None  # Modelo do veículo
    comandobloqueo: Optional[bool] = None  # True = bloquear, False = desbloquear, None = sem comando
    bloqueado: Optional[bool] = False  # Status atual de bloqueio
    comandotrocarip: Optional[bool] = None  # True = comando para trocar IP pendente
    ignicao: bool = False  # Status da ignição
    # Campos para monitoramento de bateria
    bateriavoltagem: Optional[float] = None  # Voltagem atual da bateria
    bateriabaixa: Optional[bool] = False  # True se bateria estiver baixa
    ultimoalertabateria: Optional[datetime] = None  # Timestamp do último alerta
    motion_status: Optional[str] = None  # Status de movimento do GTSTT
    motion_description: Optional[str] = None  # Descrição do movimento
    is_moving: Optional[bool] = None  # Se está em movimento
    tsusermanu: Optional[datetime] = None  # Última atualização manual

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB operations"""
        data = asdict(self)
        now = datetime.utcnow()
        if self.tsusermanu is None:
            data['tsusermanu'] = now
        return data