# GPS Tracker Service

## Overview
This project is a Python-based GPS tracking service designed to communicate with various GPS tracking devices. Its primary purpose is to receive, process, and store location and event data from these devices. The service features a robust TCP server capable of handling multiple device types, starting with GV50 devices using the Queclink @Track protocol. The vision is to create a unified tracking platform that can support a diverse range of GPS hardware, providing real-time data and control capabilities for vehicle fleets and asset management.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes
- **2025-12-23**: Converted from threading to asyncio for better performance and scalability
  - tcp_server.py: Replaced threading.Thread with asyncio.start_server()
  - database.py: Added connection pooling and async wrapper methods
  - message_handler.py: Added async versions of all database methods
  - main.py: Converted to use asyncio event loop
  - start_service.py: Updated to use asyncio.run()
  - Added test_connection.py for basic asyncio server testing

## System Architecture
The application employs a modular and service-oriented architecture with a clear separation of concerns.

### Backend Architecture
- **Service-Based Organization**: Each device type (e.g., GV50) has its own dedicated, self-contained service folder.
- **Asyncio TCP Server**: An asyncio-based server manages persistent connections with GPS devices, handling concurrent connections efficiently without thread overhead. Supports MAX_CONNECTIONS limit from environment.
- **Protocol Parser**: Device-specific parsers (e.g., for Queclink @Track) translate raw protocol messages into structured data, generating acknowledgments.
- **Message Handler**: This layer processes parsed messages, applies business logic, updates the database, tracks IP changes, and manages vehicle state. Supports both sync and async methods.
- **Database Layer**: MongoDB with connection pooling (maxPoolSize=200, minPoolSize=50). Uses MongoEngine ODM for the Vehicle model and PyMongo for VehicleData. Includes async wrapper methods using asyncio.to_thread().
- **Configuration Management**: Environment variables handle all settings for flexible deployment.
- **Logging System**: A comprehensive system provides configurable logging levels and outputs (optimized to ERROR level only for performance).

### Key Design Decisions
- **Concurrency Model**: Asyncio-based single-threaded event loop for efficient I/O handling without thread overhead. Database operations use asyncio.to_thread() for non-blocking execution.
- **Data Storage**: MongoDB was chosen for its flexible schema and high write performance, storing tracking records (`vehicle_data`) and device information (`vehicles`).
- **ORM/ODM Pattern**: MongoEngine used for Vehicle model with BaseDocument pattern providing audit fields (created_at, updated_at). VehicleData uses dataclass for lightweight tracking records.
- **Configuration**: All settings are managed via environment variables including MAX_CONNECTIONS and CONNECTION_TIMEOUT.
- **Protocol Abstraction**: The design allows for easy integration of new device protocols.
- **Command System**: Implements immediate command execution (e.g., blocking/unblocking, IP changes) via TCP, supporting bidirectional communication and real-time status updates.
- **Timestamp Handling**: Proper conversion of device timestamps to datetime objects.
- **Performance Optimization**: Logging optimized to ERROR level only for improved I/O performance. Asyncio reduces memory usage vs threading.

### Key Components
- **GV50 Service**: Contains components like `tcp_server.py` (asyncio), `protocol_parser.py`, and `message_handler.py`.
- **Database Manager (`database.py`)**: Manages both PyMongo and MongoEngine connections with connection pooling, data models, and indexing. Provides async wrapper methods.
- **Data Models (`models.py`)**: 
  - `BaseDocument`: Abstract MongoEngine Document with audit fields (created_at, updated_at)
  - `Vehicle`: MongoEngine Document extending BaseDocument for device/vehicle management with fields like IMEI, dsplaca, bloqueado, ignicao, etc.
  - `VehicleData`: Dataclass for lightweight location/tracking records
- **Configuration (`config.py`)**: Handles environment-based settings including MAX_CONNECTIONS, CONNECTION_TIMEOUT.
- **Logging (`logger.py`)**: Centralized logging for all services (ERROR level only).
- **Notification Service (`notification_service.py`)**: Firebase Cloud Messaging integration for push notifications.
- **Test Script (`test_connection.py`)**: Basic asyncio connection tests for the server.

### Push Notifications (Firebase)
The system supports push notifications via Firebase Cloud Messaging (FCM) for key vehicle events:
- **Ignition On/Off**: Notifies when vehicle ignition changes state.
- **Vehicle Blocking/Unblocking**: Notifies when blocking commands are confirmed.
- **Low Battery Alert**: Notifies when battery drops below 10V (critical) or 12V (warning).

**Token Resolution**: FCM tokens are fetched from the `customers` collection using the `fcm_token` field. The system looks up the customer associated with the vehicle via `customer_id` reference. If no token is found, falls back to topic-based notification.

Configuration:
- `PUSH_NOTIFICATIONS_ENABLED`: Set to `true` to enable notifications (default: false).
- `FIREBASE_CREDENTIALS_JSON`: JSON string with Firebase service account credentials, or place a `firebase-credentials.json` file in the gv50 folder.
- `FIREBASE_DEFAULT_TOPIC`: Fallback topic for notifications when no FCM token is found (default: vehicle_alerts).

## External Dependencies

### Database
- **MongoDB**: Primary data store with connection pooling.
  - Drivers: PyMongo (with pooling: maxPoolSize=200, minPoolSize=50) + MongoEngine ODM
  - Database Name: `tracker`
  - Collections: `vehicle_data`, `vehicles`
  - Connection String: `mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker`
  - Vehicle model uses MongoEngine with unique indexes on IMEI and dsplaca (sparse)

### Python Packages
- `pymongo`: For direct MongoDB interaction (VehicleData records) with connection pooling.
- `mongoengine`: ODM for Vehicle model with BaseDocument pattern.
- `python-dotenv`: For environment variable management.
- `asyncio`: For async TCP server and concurrent connection handling (built-in).
- `aiofiles`: For async file operations.
- `re`: For regular expressions in protocol parsing.

### Protocol Support
- **Queclink @Track Protocol V4.01**: Fully implemented for GV50 devices.
  - Supported Message Types: GTFRI (location), GTIGN/GTIGF (ignition), GTOUT (control), GTSRI (IP change), alerts, and events.
  - Message Identification: +RESP (real-time), +BUFF (buffered), +ACK (acknowledgments).
  - Bidirectional communication with automatic acknowledgment responses.
