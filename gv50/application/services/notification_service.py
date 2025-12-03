from datetime import datetime
from typing import Optional, Dict

from ...domain.interfaces.notification_gateway import NotificationGateway
from ...domain.interfaces.repositories import VehicleRepository, CustomerRepository


class NotificationService:
    """Application service for sending vehicle notifications"""
    
    def __init__(
        self,
        notification_gateway: NotificationGateway,
        vehicle_repository: VehicleRepository,
        customer_repository: CustomerRepository,
        default_topic: str = 'vehicle_alerts',
        logger=None
    ):
        self.notification_gateway = notification_gateway
        self.vehicle_repository = vehicle_repository
        self.customer_repository = customer_repository
        self.default_topic = default_topic
        self.logger = logger
    
    def _log(self, level: str, message: str):
        """Log a message if logger is available"""
        if self.logger:
            getattr(self.logger, level, self.logger.info)(message)
    
    def _get_customer_fcm_token(self, imei: str) -> Optional[str]:
        """Get FCM token from customer associated with vehicle"""
        try:
            vehicle = self.vehicle_repository.get_by_imei(imei)
            if vehicle and vehicle.customer_id:
                customer = self.customer_repository.get_by_id(vehicle.customer_id)
                if customer and customer.has_fcm_token():
                    return customer.fcm_token
            return None
        except Exception as e:
            self._log('error', f"Error getting FCM token for IMEI {imei}: {e}")
            return None
    
    def _send_notification(self, imei: str, title: str, body: str, data: Dict[str, str]) -> bool:
        """Send notification to customer's FCM token or fallback to topic"""
        if not self.notification_gateway.is_enabled():
            return False
        
        token = self._get_customer_fcm_token(imei)
        
        if token:
            self._log('info', f"Sending notification to customer token for IMEI {imei}")
            return self.notification_gateway.send_to_token(token, title, body, data)
        else:
            self._log('debug', f"No FCM token found for IMEI {imei}, using topic fallback")
            return self.notification_gateway.send_to_topic(self.default_topic, title, body, data)
    
    def is_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self.notification_gateway.is_enabled()
    
    def notify_ignition_on(self, imei: str, placa: Optional[str] = None) -> bool:
        """Send notification when vehicle ignition turns ON"""
        if not self.is_enabled():
            return False
        
        vehicle_id = placa or imei
        title = "Veiculo Ligado"
        body = f"O veiculo {vehicle_id} foi ligado"
        data = {
            "event_type": "ignition_on",
            "imei": imei,
            "placa": placa or "",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_notification(imei, title, body, data)
    
    def notify_ignition_off(self, imei: str, placa: Optional[str] = None) -> bool:
        """Send notification when vehicle ignition turns OFF"""
        if not self.is_enabled():
            return False
        
        vehicle_id = placa or imei
        title = "Veiculo Desligado"
        body = f"O veiculo {vehicle_id} foi desligado"
        data = {
            "event_type": "ignition_off",
            "imei": imei,
            "placa": placa or "",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_notification(imei, title, body, data)
    
    def notify_vehicle_blocked(self, imei: str, placa: Optional[str] = None) -> bool:
        """Send notification when vehicle is blocked"""
        if not self.is_enabled():
            return False
        
        vehicle_id = placa or imei
        title = "Veiculo Bloqueado"
        body = f"O veiculo {vehicle_id} foi bloqueado com sucesso"
        data = {
            "event_type": "vehicle_blocked",
            "imei": imei,
            "placa": placa or "",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_notification(imei, title, body, data)
    
    def notify_vehicle_unblocked(self, imei: str, placa: Optional[str] = None) -> bool:
        """Send notification when vehicle is unblocked"""
        if not self.is_enabled():
            return False
        
        vehicle_id = placa or imei
        title = "Veiculo Desbloqueado"
        body = f"O veiculo {vehicle_id} foi desbloqueado com sucesso"
        data = {
            "event_type": "vehicle_unblocked",
            "imei": imei,
            "placa": placa or "",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_notification(imei, title, body, data)
    
    def notify_low_battery(self, imei: str, voltage: float, placa: Optional[str] = None) -> bool:
        """Send notification when vehicle battery is low"""
        if not self.is_enabled():
            return False
        
        vehicle_id = placa or imei
        title = "Bateria Baixa"
        body = f"O veiculo {vehicle_id} esta com bateria baixa ({voltage}V)"
        data = {
            "event_type": "low_battery",
            "imei": imei,
            "placa": placa or "",
            "voltage": str(voltage),
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_notification(imei, title, body, data)
