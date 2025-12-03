from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Customer:
    """Customer entity - read-only fields for customer data"""
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    document: Optional[str] = None
    phone: Optional[str] = None
    fcm_token: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def has_fcm_token(self) -> bool:
        """Check if customer has a valid FCM token"""
        return self.fcm_token is not None and len(self.fcm_token) > 0
