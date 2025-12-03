from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from ..entities.customer import Customer
from ..entities.vehicle import Vehicle


class CustomerRepository(ABC):
    """Interface for Customer repository"""
    
    @abstractmethod
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        pass
    
    @abstractmethod
    def get_by_document(self, document: str) -> Optional[Customer]:
        """Get customer by document"""
        pass


class VehicleRepository(ABC):
    """Interface for Vehicle repository"""
    
    @abstractmethod
    def get_by_imei(self, imei: str) -> Optional[Vehicle]:
        """Get vehicle by IMEI"""
        pass
    
    @abstractmethod
    def get_by_plate(self, plate: str) -> Optional[Vehicle]:
        """Get vehicle by plate (dsplaca)"""
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: str) -> List[Vehicle]:
        """Get all vehicles for a customer"""
        pass
    
    @abstractmethod
    def save(self, vehicle: Vehicle) -> Vehicle:
        """Save or update vehicle"""
        pass
    
    @abstractmethod
    def upsert(self, vehicle_data: Dict[str, Any]) -> bool:
        """Upsert vehicle data by IMEI"""
        pass
