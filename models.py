from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class VehicleData:
    """Vehicle tracking data model"""
    imei: str
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    altitude: Optional[str] = None
    speed: Optional[str] = None
    course: Optional[str] = None
    ignition: Optional[bool] = None
    battery_level: Optional[str] = None
    gsm_signal: Optional[str] = None
    gps_accuracy: Optional[str] = None
    device_timestamp: Optional[str] = None
    server_timestamp: Optional[datetime] = None
    raw_message: Optional[str] = None  # Mensagem original completa recebida do GPS
    message_type: Optional[str] = None
    report_type: Optional[str] = None
    mensagem_raw: Optional[str] = None  # Mensagem original completa recebida do GPS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        data = asdict(self)
        if self.server_timestamp is None:
            data['server_timestamp'] = datetime.utcnow()
        return data

@dataclass
class Vehicle:
    """Vehicle information model"""
    imei: str
    plate_number: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    owner_cpf: Optional[str] = None
    chip_number: Optional[str] = None
    is_blocked: Optional[bool] = False
    block_command_pending: Optional[bool] = False
    block_notification_sent: Optional[bool] = False
    ignition_status: Optional[bool] = None
    battery_level: Optional[str] = None
    last_location: Optional[Dict[str, str]] = None
    last_update: Optional[datetime] = None
    last_raw_message: Optional[str] = None
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

@dataclass
class EventLog:
    """Event log model"""
    imei: str
    event_type: str  # 'ignition_on', 'ignition_off', 'block', 'unblock', 'battery_low', 'ip_change'
    event_data: Optional[Dict[str, Any]] = None
    raw_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    processed: Optional[bool] = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        data = asdict(self)
        if self.timestamp is None:
            data['timestamp'] = datetime.utcnow()
        return data

@dataclass
class MessageLog:
    """Message log model for all device communications"""
    imei: str
    client_ip: str
    message_direction: str  # 'incoming' or 'outgoing'
    raw_message: str
    message_type: Optional[str] = None
    report_type: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        data = asdict(self)
        if self.timestamp is None:
            data['timestamp'] = datetime.utcnow()
        return data

@dataclass
class IPChangeLog:
    """IP change tracking model"""
    imei: str
    old_ip: Optional[str] = None
    new_ip: str = None
    change_reason: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        data = asdict(self)
        if self.timestamp is None:
            data['timestamp'] = datetime.utcnow()
        return data

@dataclass
class VehicleCommands:
    """Vehicle commands lookup model - apenas for command lookup, não para salvar dados"""
    imei: str
    plate_number: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    owner_cpf: Optional[str] = None
    chip_number: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    chassis_number: Optional[str] = None
    renavam: Optional[str] = None
    vehicle_type: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_number: Optional[str] = None
    registration_city: Optional[str] = None
    registration_state: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    contract_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    service_plan: Optional[str] = None
    status: Optional[str] = "active"
    notes: Optional[str] = None
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

@dataclass
class BatteryEvent:
    """Battery level event model"""
    imei: str
    battery_level: str
    battery_voltage: Optional[str] = None
    charging_status: Optional[bool] = None
    low_battery_alert: Optional[bool] = False
    critical_battery_alert: Optional[bool] = False
    external_power_status: Optional[bool] = None
    timestamp: Optional[datetime] = None
    raw_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        data = asdict(self)
        if self.timestamp is None:
            data['timestamp'] = datetime.utcnow()
        return data
