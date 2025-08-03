# GPS Tracker Service

## Overview
This project is a Python-based GPS tracking service designed to communicate with various GPS tracking devices. Its primary purpose is to receive, process, and store location and event data from these devices. The service features a robust TCP server capable of handling multiple device types, starting with GV50 devices using the Queclink @Track protocol. The vision is to create a unified tracking platform that can support a diverse range of GPS hardware, providing real-time data and control capabilities for vehicle fleets and asset management.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application employs a modular and service-oriented architecture with a clear separation of concerns.

### Backend Architecture
- **Service-Based Organization**: Each device type (e.g., GV50) has its own dedicated, self-contained service folder.
- **TCP Server**: A custom socket-based server manages persistent connections with GPS devices, handling up to 100 concurrent connections. It includes IP whitelisting/blacklisting for security.
- **Protocol Parser**: Device-specific parsers (e.g., for Queclink @Track) translate raw protocol messages into structured data, generating acknowledgments.
- **Message Handler**: This layer processes parsed messages, applies business logic, updates the database, tracks IP changes, and manages vehicle state.
- **Database Layer**: MongoDB is used as the primary storage, with a unified 'tracker' database supporting various device types.
- **Configuration Management**: Environment variables handle all settings for flexible deployment.
- **Logging System**: A comprehensive system provides configurable logging levels and outputs.

### Key Design Decisions
- **Concurrency Model**: Each GPS device connection is handled in its own thread to support concurrent devices.
- **Data Storage**: MongoDB was chosen for its flexible schema and high write performance, storing tracking records (`vehicle_data`) and device information (`vehicles`).
- **Configuration**: All settings are managed via environment variables.
- **Protocol Abstraction**: The design allows for easy integration of new device protocols.
- **Command System**: Implements immediate command execution (e.g., blocking/unblocking, IP changes) via TCP, supporting bidirectional communication and real-time status updates.
- **Timestamp Handling**: Proper conversion of device timestamps to datetime objects.

### Key Components
- **GV50 Service**: Contains components like `tcp_server.py`, `protocol_parser.py`, and `message_handler.py`.
- **Database Manager (`database.py`)**: Manages MongoDB connections, data models, and indexing.
- **Data Models (`models.py`)**: Defines `VehicleData` for location records and `Vehicle` for device/vehicle status.
- **Configuration (`config.py`)**: Handles environment-based settings.
- **Logging (`logger.py`)**: Centralized logging for all services.

## External Dependencies

### Database
- **MongoDB**: Primary data store.
  - Driver: PyMongo
  - Database Name: `tracker`
  - Collections: `vehicle_data`, `vehicles`
  - Connection String: `mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker`

### Python Packages
- `pymongo`: For MongoDB interaction.
- `python-dotenv`: For environment variable management.
- `socket`: For TCP network communication.
- `threading`: For concurrent connection handling.
- `re`: For regular expressions in protocol parsing.

### Protocol Support
- **Queclink @Track Protocol V4.01**: Fully implemented for GV50 devices.
  - Supported Message Types: GTFRI (location), GTIGN/GTIGF (ignition), GTOUT (control), GTSRI (IP change), alerts, and events.
  - Message Identification: +RESP (real-time), +BUFF (buffered), +ACK (acknowledgments).
  - Bidirectional communication with automatic acknowledgment responses.