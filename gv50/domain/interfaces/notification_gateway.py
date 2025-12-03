from abc import ABC, abstractmethod
from typing import Optional, Dict


class NotificationGateway(ABC):
    """Interface for notification gateway (Firebase, etc)"""
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if notifications are enabled"""
        pass
    
    @abstractmethod
    def send_to_token(self, token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
        """Send notification to a specific device token"""
        pass
    
    @abstractmethod
    def send_to_topic(self, topic: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
        """Send notification to a topic"""
        pass
