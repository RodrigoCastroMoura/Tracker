import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from ...domain.interfaces.notification_gateway import NotificationGateway

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


class FirebaseNotificationGateway(NotificationGateway):
    """Firebase Cloud Messaging implementation of NotificationGateway"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.initialized = False
        self.enabled = False
        self._load_config()
        
        if self.enabled and FIREBASE_AVAILABLE:
            self._initialize_firebase()
    
    def _log(self, level: str, message: str):
        """Log a message if logger is available"""
        if self.logger:
            getattr(self.logger, level, self.logger.info)(message)
    
    def _load_config(self):
        """Load notification configuration from environment variables"""
        self.enabled = os.getenv('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        self.credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
        self.default_topic = os.getenv('FIREBASE_DEFAULT_TOPIC', 'vehicle_alerts')
        
        if not self.enabled:
            self._log('info', "Push notifications are DISABLED (PUSH_NOTIFICATIONS_ENABLED=false)")
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if firebase_admin._apps:
                self.initialized = True
                self._log('info', "Firebase already initialized")
                return
            
            if os.path.exists(self.credentials_path):
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                self._log('info', "Firebase initialized successfully from credentials file")
            else:
                firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
                if firebase_creds_json:
                    cred_dict = json.loads(firebase_creds_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    self.initialized = True
                    self._log('info', "Firebase initialized successfully from environment variable")
                else:
                    self._log('warning', f"Firebase credentials not found at {self.credentials_path} or in FIREBASE_CREDENTIALS_JSON")
                    self.enabled = False
                    
        except Exception as e:
            self._log('error', f"Failed to initialize Firebase: {e}")
            self.enabled = False
            self.initialized = False
    
    def is_enabled(self) -> bool:
        """Check if push notifications are enabled and initialized"""
        return self.enabled and self.initialized and FIREBASE_AVAILABLE
    
    def send_to_token(self, token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
        """Send notification to a specific device token"""
        if not self.is_enabled():
            self._log('debug', "Push notifications disabled, skipping send_to_token")
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
            self._log('info', f"Push notification sent to device: {title}")
            return True
            
        except Exception as e:
            self._log('error', f"Failed to send push notification to device: {e}")
            return False
    
    def send_to_topic(self, topic: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
        """Send notification to a Firebase topic"""
        if not self.is_enabled():
            self._log('debug', "Push notifications disabled, skipping send_to_topic")
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
            self._log('info', f"Push notification sent to topic '{topic}': {title}")
            return True
            
        except Exception as e:
            self._log('error', f"Failed to send push notification to topic '{topic}': {e}")
            return False
    
    def send_to_tokens(self, tokens: List[str], title: str, body: str, data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send notification to multiple device tokens"""
        if not self.is_enabled():
            self._log('debug', "Push notifications disabled, skipping send_to_tokens")
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
            self._log('info', f"Push notification sent to {response.success_count} devices, {response.failure_count} failed")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
            
        except Exception as e:
            self._log('error', f"Failed to send push notification to multiple devices: {e}")
            return {"success_count": 0, "failure_count": len(tokens)}
