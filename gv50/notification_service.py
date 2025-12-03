import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from logger import logger

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase Admin SDK not installed. Push notifications disabled.")

from database import db_manager

class NotificationService:
    """Service for sending Firebase Cloud Messaging push notifications"""
    
    def __init__(self):
        self.initialized = False
        self.enabled = False
        self._load_config()
        
        if self.enabled and FIREBASE_AVAILABLE:
            self._initialize_firebase()
    
    def _load_config(self):
        """Load notification configuration from environment variables"""
        self.enabled = os.getenv('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        self.credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
        self.default_topic = os.getenv('FIREBASE_DEFAULT_TOPIC', 'vehicle_alerts')
        
        if not self.enabled:
            logger.info("Push notifications are DISABLED (PUSH_NOTIFICATIONS_ENABLED=false)")
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if firebase_admin._apps:
                self.initialized = True
                logger.info("Firebase already initialized")
                return
            
            if os.path.exists(self.credentials_path):
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                logger.info("Firebase initialized successfully from credentials file")
            else:
                firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
                if firebase_creds_json:
                    cred_dict = json.loads(firebase_creds_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    self.initialized = True
                    logger.info("Firebase initialized successfully from environment variable")
                else:
                    logger.warning(f"Firebase credentials not found at {self.credentials_path} or in FIREBASE_CREDENTIALS_JSON")
                    self.enabled = False
                    
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.enabled = False
            self.initialized = False
    
    def is_enabled(self) -> bool:
        """Check if push notifications are enabled and initialized"""
        return self.enabled and self.initialized and FIREBASE_AVAILABLE
    
    def _get_vehicle_fcm_token(self, imei: str) -> Optional[str]:
        """Get FCM token from vehicle record by IMEI"""
        try:
            vehicle = db_manager.get_vehicle_by_imei(imei)
            if vehicle:
                return vehicle.get('token_fcm') or vehicle.get('fcm_token')
            return None
        except Exception as e:
            logger.error(f"Error getting FCM token for IMEI {imei}: {e}")
            return None
    
    def _send_notification(self, imei: str, title: str, body: str, data: Dict[str, str]) -> bool:
        """Send notification to vehicle's FCM token or fallback to topic"""
        if not self.is_enabled():
            return False
        
        token = self._get_vehicle_fcm_token(imei)
        
        if token:
            return self.send_to_token(token, title, body, data)
        else:
            logger.debug(f"No FCM token found for IMEI {imei}, using topic fallback")
            return self.send_to_topic(self.default_topic, title, body, data)
    
    def send_to_topic(self, topic: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
        """Send notification to a Firebase topic"""
        if not self.is_enabled():
            logger.debug("Push notifications disabled, skipping send_to_topic")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
            )
            
            response = messaging.send(message)
            logger.info(f"Push notification sent to topic '{topic}': {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification to topic '{topic}': {e}")
            return False
    
    def send_to_token(self, token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
        """Send notification to a specific device token"""
        if not self.is_enabled():
            logger.debug("Push notifications disabled, skipping send_to_token")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )
            
            response = messaging.send(message)
            logger.info(f"Push notification sent to device: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification to device: {e}")
            return False
    
    def send_to_tokens(self, tokens: List[str], title: str, body: str, data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send notification to multiple device tokens"""
        if not self.is_enabled():
            logger.debug("Push notifications disabled, skipping send_to_tokens")
            return {"success_count": 0, "failure_count": 0}
        
        if not tokens:
            return {"success_count": 0, "failure_count": 0}
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
            )
            
            response = messaging.send_each_for_multicast(message)
            logger.info(f"Push notification sent to {response.success_count} devices, {response.failure_count} failed")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
            
        except Exception as e:
            logger.error(f"Failed to send push notification to multiple devices: {e}")
            return {"success_count": 0, "failure_count": len(tokens)}
    
    def notify_ignition_on(self, imei: str, placa: Optional[str] = None):
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
    
    def notify_ignition_off(self, imei: str, placa: Optional[str] = None):
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
    
    def notify_vehicle_blocked(self, imei: str, placa: Optional[str] = None):
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
    
    def notify_vehicle_unblocked(self, imei: str, placa: Optional[str] = None):
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
    
    def notify_low_battery(self, imei: str, voltage: float, placa: Optional[str] = None):
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


notification_service = NotificationService()
