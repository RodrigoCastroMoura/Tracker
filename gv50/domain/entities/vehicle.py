from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class Vehicle:
    """Vehicle entity - represents a GPS tracked vehicle"""
    id: Optional[str] = None
    imei: Optional[str] = None
    dsplaca: Optional[str] = None
    customer_id: Optional[str] = None
    bloqueado: bool = False
    ignicao: bool = False
    comandobloqueo: Optional[bool] = None
    bateriavoltagem: Optional[float] = None
    bateriabaixa: bool = False
    ultimoalertabateria: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    velocidade: Optional[float] = None
    direcao: Optional[float] = None
    altitude: Optional[float] = None
    odometro: Optional[float] = None
    horimetro: Optional[float] = None
    ultimo_ip: Optional[str] = None
    ip_antigo: Optional[str] = None
    tsrastreador: Optional[datetime] = None
    tsusermanu: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_identifier(self) -> str:
        """Get vehicle identifier (plate or IMEI)"""
        return self.dsplaca or self.imei or "Unknown"
    
    def is_blocked(self) -> bool:
        """Check if vehicle is blocked"""
        return self.bloqueado
    
    def is_ignition_on(self) -> bool:
        """Check if ignition is on"""
        return self.ignicao
    
    def has_low_battery(self, threshold: float = 12.0) -> bool:
        """Check if battery is below threshold"""
        if self.bateriavoltagem is None:
            return False
        return self.bateriavoltagem < threshold
    
    def has_critical_battery(self, threshold: float = 10.0) -> bool:
        """Check if battery is critically low"""
        if self.bateriavoltagem is None:
            return False
        return self.bateriavoltagem < threshold
