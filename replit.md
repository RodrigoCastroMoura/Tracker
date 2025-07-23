# GV50 Tracker Service

## Overview

This is a comprehensive Python-based GPS tracking service designed specifically for GV50 GPS tracking devices. The service implements a robust TCP server that communicates with GPS devices using the Queclink @Track protocol, processes incoming location and event data, and stores it in a MongoDB database. The system provides complete raw message preservation, extensive logging capabilities, and support for vehicle control commands including blocking/unblocking functionality.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (July 23, 2025)

✓ Complete service implementation with MongoDB integration
✓ Added comprehensive message logging and preservation system  
✓ Implemented IP change tracking with environment-based control
✓ Created battery event monitoring and alert system
✓ Added vehicle commands lookup table structure
✓ Integrated ignition status tracking and updates
✓ Environment-based configuration for all logging options
✓ Complete raw message storage with mensagem_raw field
✓ Message type identification (+RESP, +BUFF, +ACK)
✓ TCP server running on port 5000 with concurrent connection support
✓ Fixed all MongoDB connection issues and method name conflicts
✓ Corrected TCP server message handling to use proper method names
✓ Resolved Vehicle model initialization with MongoDB _id field filtering
✓ Successfully tested with multiple GV50 message types (GTFRI, GTIGN, GTIGF)
✓ Confirmed data persistence with 7 records stored across both tables
✓ System fully operational and processing GPS tracking data correctly
✓ Updated VehicleData model: removed 'course' field, added 'timestamp' and 'deviceTimestamp' fields
✓ All field names now follow English standard: timestamp (datetime), deviceTimestamp (string)
✓ Tested new structure with successful data storage and field validation

## System Architecture

The application follows a modular architecture with clear separation of concerns:

### Backend Architecture
- **TCP Server**: Custom socket-based server for handling persistent connections with GPS devices
- **Protocol Parser**: Dedicated parser for Queclink @Track protocol messages
- **Message Handler**: Business logic layer for processing parsed messages and database operations
- **Database Layer**: MongoDB integration with connection management and data models
- **Configuration Management**: Environment-based configuration with sensible defaults
- **Logging System**: Comprehensive logging with configurable levels and outputs

### Key Design Decisions
- **Single-threaded per connection**: Each GPS device connection is handled in its own thread to support concurrent devices
- **MongoDB for storage**: NoSQL database chosen for flexible schema and high write performance
- **Environment-based configuration**: All settings configurable via environment variables for deployment flexibility
- **Protocol abstraction**: Parser is designed to handle multiple message types from the Queclink protocol

## Key Components

### TCP Server (`tcp_server.py`)
- Manages incoming TCP connections from GPS devices
- Implements IP whitelisting/blacklisting for security
- Handles connection lifecycle and cleanup
- Supports up to 100 concurrent device connections

### Protocol Parser (`protocol_parser.py`)
- Parses Queclink @Track protocol messages
- Supports multiple message types (GTFRI, GTIGN, GTIGF, etc.)
- Generates acknowledgment responses for devices
- Extracts GPS coordinates, speed, ignition status, and other telemetry data

### Message Handler (`message_handler.py`)
- Processes parsed messages and updates database
- Handles different message types (reports, acknowledgments, events)
- Tracks IP address changes for devices
- Manages vehicle state updates

### Database Manager (`database.py`)
- Manages MongoDB connections and operations
- Implements data models for vehicles, tracking data, and logs
- Creates appropriate indexes for performance
- Handles connection failures and retries

### Data Models (`models.py`)
- **VehicleData**: Individual GPS tracking records with 9 specific fields:
  - imei, longitude, latitude, altitude, speed, ignition, battery_level, timestamp (server timestamp), deviceTimestamp (device timestamp), mensagem_raw
- **Vehicle**: Device/vehicle information, current status, control states, ignition status, and battery levels

## Data Flow

1. **Device Connection**: GPS device establishes TCP connection to server
2. **Message Reception**: Server receives raw protocol messages
3. **Protocol Parsing**: Messages are parsed according to Queclink @Track protocol
4. **Data Processing**: Parsed data is processed and validated
5. **Database Storage**: Vehicle data and events are stored in MongoDB
6. **Acknowledgment**: Server sends acknowledgment response to device
7. **Connection Management**: Server maintains persistent connections with heartbeat monitoring

## External Dependencies

### Database
- **MongoDB**: Primary data storage using PyMongo driver  
- Connection: `mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/gv50_tracker`
- Collections: `vehicle_data`, `vehicles` (only 2 tables as requested)
- Automatic indexing for optimal query performance

### Python Packages
- `pymongo`: MongoDB database driver with full feature support
- `python-dotenv`: Environment variable management and configuration
- `logging`: Built-in Python logging with custom formatting
- `socket`: TCP network communication and connection handling
- `threading`: Concurrent connection handling for multiple devices
- `re`: Regular expressions for protocol parsing and validation

### Protocol Support
- **Queclink @Track Protocol V4.01**: Complete implementation for GV50 devices
- Message types: GTFRI (location), GTIGN/GTIGF (ignition), GTOUT (control), alerts, and events
- Message identification: +RESP (real-time), +BUFF (buffered), +ACK (acknowledgments)
- Bidirectional communication with acknowledgment responses

## Deployment Strategy

### Configuration
- All settings managed through environment variables
- `.env` file support for local development
- Configurable logging levels and outputs
- IP access control with whitelist/blacklist support

### Scalability Considerations
- Thread-per-connection model supports moderate device loads
- MongoDB provides horizontal scaling capabilities
- Logging system supports both file and console output
- Configurable connection timeouts and heartbeat intervals

### Security Features
- IP address filtering (whitelist/blacklist)
- Connection timeout management
- Comprehensive audit logging
- Raw message logging for debugging and compliance

### Monitoring and Logging
- Configurable logging levels (DEBUG, INFO, WARNING, ERROR)
- Separate logs for incoming/outgoing messages (controllable via .env)
- Database operation logging with performance metrics
- Service statistics tracking (connections, messages, uptime)
- IP change tracking and alerting system
- Raw message preservation for debugging and compliance

## Key Features Implemented

### Message Processing & Storage
- **Complete Raw Message Preservation**: All messages stored with `mensagem_raw` field
- **Message Type Identification**: Automatic detection of +RESP, +BUFF, +ACK message types
- **Bidirectional Communication Logging**: All incoming and outgoing messages tracked
- **Environment-Controlled Logging**: All logging options configurable via .env file

### Device Management & Control
- **Vehicle Blocking/Unblocking**: Complete GTOUT command processing with status tracking
- **Ignition Status Updates**: Real-time ignition on/off detection and vehicle status updates
- **IP Change Monitoring**: Automatic detection and logging of device IP changes
- **Battery Event Processing**: Low/critical battery alerts with configurable thresholds

### Database Architecture (Simplified - 2 Tables Only)
- **vehicle_data**: Primary tracking data with GPS coordinates, speed, altitude, raw messages, and all GPS events
- **vehicles**: Device information with current status, control states, ignition status, and battery levels

### Configuration Management
- **Environment-Based Setup**: All settings via .env file including logging controls
- **IP Access Control**: Configurable whitelist/blacklist via ALLOWED_IPS/BLOCKED_IPS
- **MongoDB Integration**: Direct connection to provided MongoDB cluster
- **Port Configuration**: Service running on port 5000 as specified

### Protocol Support
- **Full GV50 Compatibility**: Complete Queclink @Track protocol implementation
- **Multi-Message Support**: GTFRI, GTIGN, GTIGF, GTOUT, alerts, and buffered messages
- **Acknowledgment Generation**: Automatic ACK responses to maintain device communication
- **Error Handling**: Robust parsing with comprehensive error logging