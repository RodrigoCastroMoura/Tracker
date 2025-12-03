# GPS Tracker Service

## Overview
This project is a Python-based GPS tracking service designed to communicate with various GPS tracking devices. Its primary purpose is to receive, process, and store location and event data from these devices. The service features a robust TCP server capable of handling multiple device types, starting with GV50 devices using the Queclink @Track protocol. The vision is to create a unified tracking platform that can support a diverse range of GPS hardware, providing real-time data and control capabilities for vehicle fleets and asset management.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application follows **Clean Architecture** principles with clear separation of concerns across layers.

### Project Structure (Clean Architecture)
```
gv50/
├── domain/                    # Domain Layer - Business Logic
│   ├── entities/              # Domain entities (Customer, Vehicle)
│   └── interfaces/            # Repository and gateway interfaces
├── application/               # Application Layer - Use Cases
│   ├── services/              # Application services (NotificationService)
│   └── use_cases/             # Business use cases
├── infrastructure/            # Infrastructure Layer - External Concerns
│   ├── database/              # MongoDB models and repositories
│   ├── firebase/              # Firebase notification gateway
│   └── config/                # Configuration management
├── presentation/              # Presentation Layer - External Interfaces
│   └── tcp/                   # TCP server handlers
└── [legacy files]             # Original files (being migrated)
```

### Backend Architecture
- **Clean Architecture**: Organized in layers (Domain, Application, Infrastructure, Presentation)
- **TCP Server**: Custom socket-based server managing persistent connections with GPS devices
- **Protocol Parser**: Device-specific parsers translating raw protocol messages
- **Message Handler**: Processes parsed messages and applies business logic
- **Database Layer**: MongoDB with MongoEngine ODM for models
- **Notification System**: Firebase Cloud Messaging for push notifications

### Key Design Decisions
- **Clean Architecture**: Separation of concerns with dependency inversion
- **Domain-Driven Design**: Customer and Vehicle as core domain entities
- **Repository Pattern**: Interfaces for data access abstraction
- **Gateway Pattern**: Notification gateway interface for external services
- **Concurrency Model**: Thread-per-connection for GPS device handling

### Data Models

#### Customer (Read-Only)
- `id`: Unique identifier
- `name`: Customer name
- `email`: Email address
- `document`: CPF/CNPJ document
- `phone`: Phone number
- `fcm_token`: Firebase Cloud Messaging token for push notifications

#### Vehicle
- `IMEI`: Device identifier (required)
- `dsplaca`: License plate
- `customer_id`: Reference to Customer (owner)
- `bloqueado`: Blocking status
- `ignicao`: Ignition status
- `bateriavoltagem`: Battery voltage
- Other tracking fields...

### Push Notifications (Firebase)
The system supports push notifications via Firebase Cloud Messaging (FCM) for key vehicle events:
- **Ignition On/Off**: Notifies when vehicle ignition changes state
- **Vehicle Blocking/Unblocking**: Notifies when blocking commands are confirmed
- **Low Battery Alert**: Notifies when battery drops below threshold

**Token Resolution**: FCM tokens are fetched from the `customers` collection using the `fcm_token` field. The system:
1. Looks up the vehicle by IMEI
2. Gets the associated customer via `customer_id`
3. Sends notification to customer's `fcm_token`
4. Falls back to topic-based notification if no token found

Configuration:
- `PUSH_NOTIFICATIONS_ENABLED`: Set to `true` to enable notifications (default: false)
- `FIREBASE_CREDENTIALS_JSON`: JSON string with Firebase service account credentials
- `FIREBASE_DEFAULT_TOPIC`: Fallback topic for notifications (default: vehicle_alerts)

## External Dependencies

### Database
- **MongoDB**: Primary data store.
  - Drivers: PyMongo + MongoEngine ODM
  - Database Name: `tracker`
  - Collections: `vehicle_data`, `vehicles`
  - Connection String: `mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker`
  - Vehicle model uses MongoEngine with unique indexes on IMEI and dsplaca (sparse)

### Python Packages
- `pymongo`: For direct MongoDB interaction (VehicleData records).
- `mongoengine`: ODM for Vehicle model with BaseDocument pattern.
- `python-dotenv`: For environment variable management.
- `socket`: For TCP network communication.
- `threading`: For concurrent connection handling.
- `re`: For regular expressions in protocol parsing.

### Protocol Support
- **Queclink @Track Protocol V4.01**: Fully implemented for GV50 devices.
  - Supported Message Types: GTFRI (location), GTIGN/GTIGF (ignition), GTOUT (control), GTSRI (IP change), alerts, and events.
  - Message Identification: +RESP (real-time), +BUFF (buffered), +ACK (acknowledgments).
  - Bidirectional communication with automatic acknowledgment responses.