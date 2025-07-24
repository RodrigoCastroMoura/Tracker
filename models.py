from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class VehicleData:
    """Vehicle tracking data model - apenas campos solicitados"""
    imei: str
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    altitude: Optional[str] = None
    speed: Optional[str] = None
    ignition: Optional[bool] = None
    battery_level: Optional[str] = None
    timestamp: Optional[datetime] = None
    deviceTimestamp: str = ""
    systemDate: Optional[datetime] = None
    mensagem_raw: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        return asdict(self)

@dataclass
class Vehicle:
    """Vehicle information model - tabela para informações dos veículos"""
    imei: str
    plate_number: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    owner_cpf: Optional[str] = None
    chip_number: Optional[str] = None
    is_blocked: Optional[bool] = False
    ignition_status: Optional[bool] = None
    battery_level: Optional[str] = None
    last_location: Optional[Dict[str, str]] = None
    last_update: Optional[datetime] = None
    last_raw_message: Optional[str] = None
    current_ip: Optional[str] = None
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB operations"""
        data = asdict(self)
        now = datetime.utcnow()
        if self.created_at is None:
            data['created_at'] = now
        data['updated_at'] = now
        return data