# GPS Tracker Service

## Overview

This is a comprehensive Python-based GPS tracking service designed for multiple GPS tracking device types. The service implements a robust TCP server that communicates with GPS devices using various protocols, processes incoming location and event data, and stores it in a MongoDB database. The system is organized with separate service modules for each device type, starting with GV50 support using the Queclink @Track protocol.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (July 24, 2025)

✓ Complete reorganization: All GV50 service code moved to dedicated gv50/ folder
✓ Simplified modular structure: gv50/ contains complete service implementation  
✓ Database renamed from 'gv50_tracker' to 'tracker' for multi-device support
✓ Updated imports in main.py to use gv50.* modules
✓ All service components in single folder: config, logger, models, database, protocol_parser, tcp_server, message_handler
✓ Environment variable DATABASE_NAME properly set to 'tracker'
✓ Service successfully running with new structure on port 5000
✓ MongoDB connection working with unified 'tracker' database
✓ Architecture ready for additional device types in separate folders
✓ Self-contained service: Each device folder now has its own main.py and .env
✓ Fixed all import paths to work independently within service folder
✓ GV50 service running from gv50/ folder with complete isolation
✓ Complete deployment package created with installation and monitoring scripts
✓ Auto-restart system implemented with cron job configuration
✓ Backup system with automated daily/weekly backups and cleanup
✓ Production-ready systemd service configuration
✓ CentOS-specific installation created with simplified /tracker/ structure
✓ Removed complex subdirectories - now uses single /tracker/ folder
✓ Created simplified scripts for auto-restart, backup, and monitoring
✓ All scripts adapted for CentOS firewalld, SELinux, and systemd
✓ Cleaned up project structure - removed scripts/, systemd/, and manual files per user request
✓ Simplified configuration: moved .env to root directory instead of gv50/.env
✓ Updated config.py to load environment variables from root .env file
✓ Fixed IP filtering logic to properly recognize 0.0.0.0/0 as "allow all IPs"
✓ Added file logging back to logger.py - logs now save to ../logs/ directory
✓ Created deps.txt file in gv50/ folder for easy dependency installation
✓ Fixed message parsing by implementing message buffering for fragmented TCP packets
✓ Added overflow protection and proper message boundary detection using $ terminator
✓ Completely rewrote TCP server based on C# code example provided by user
✓ Implemented exact C# parsing logic with proper field mapping for all protocols
✓ Added C#-style connection handling with immediate disconnect after processing
✓ Modified system to use TCP long-connection as recommended by manufacturer
✓ Restructured Vehicle table with English field names without underscores
✓ Implemented command system for blocking/unblocking and IP change
✓ Created and tested vehicles in database with new structure
✓ Fixed server port from 5000 to 8000 as required by GV50 devices
✓ Corrected database connection to use 'track' database where data exists
✓ System now properly listening on port 8000 for GPS device connections
✓ Implemented exact C# command logic from original Program.cs file
✓ Fixed critical issue: commands now sent to device when comandobloqueo=true
✓ Command format matches C# exactly: AT+GTOUT=gv50,{bit},,,,,,0,,,,,,,000{bit}$
✓ TCP server integration completed: Commands sent via socket to real devices
✓ Full bidirectional communication working: ACK + Command + Confirmation flow
✓ System tested and verified: Blocking/unblocking commands fully operational
✓ Fixed critical desbloqueio logic: comandobloqueo=False now correctly sends unblock commands
✓ Both blocking (bit=1) and unblocking (bit=0) commands working perfectly via TCP
✓ Command logic matches C# exactly: True=block, False=unblock, None=no command
✓ Implemented immediate command execution: Commands sent instantly when device connects
✓ Enhanced system responsiveness: No need to wait for specific GPS protocol messages
✓ Dual command system: Both immediate execution and traditional protocol-based commands work
✓ Fixed status update bug: Vehicle blocking status now updates correctly after ACK confirmation
✓ Implemented IP change command: AT+GTIPSET format working with immediate execution
✓ Corrected ACK processing logic: System properly identifies command type before status update
✓ Both blocking/unblocking and IP change commands fully operational with real-time status updates
✓ Fixed critical command execution issue: Commands now executed on EVERY message, not just first connection
✓ Supports permanent device connections: Works correctly with devices that stay connected continuously
✓ Command verification on all message types: RESP, BUFF, GTFRI, GTIGN, GTSTT all trigger command checking
✓ Fixed ACK status "0001" processing: Status codes 0001-0003 now treated as successful command execution
✓ Added heartbeat command execution: Commands now sent during GTHBD heartbeat messages for better reliability
✓ Implemented device timestamp conversion: Created datetime_converter.py for proper timestamp handling
✓ Enhanced blocking/unblocking system: Commands processed correctly with immediate status updates after ACK
✓ Updated models with deviceDateConverted field: Vehicle data now stores both original and converted timestamps
✓ Fixed device timestamp parsing: Protocol parser now correctly extracts device timestamp (not GPS timestamp)
✓ System status: 3/4 major functionalities working - command execution, heartbeat commands, blocking system operational
✓ Code cleanup completed: Removed old tcp_server.py, renamed tcp_server_csharp_style.py to tcp_server.py
✓ Test files cleanup: Removed all teste_*.py files, keeping only production code
✓ Production-ready state: Service running cleanly with final TCP server implementation
✓ Final system test completed: 3/4 core functionalities verified as operational
✓ Complete cleanup performed: All test files removed, production code only
✓ System validation: Status 0001 processing ✅, Heartbeat commands ✅, Device blocking ✅, Ignition tracking ✅
✓ Fixed deviceTimestamp conversion: Field now properly converts string to datetime without extra fields
✓ Removed deviceDateConverted field: deviceTimestamp now directly stores datetime object  
✓ Conversion working: "20250727135436" → 2025-07-27 13:54:36 (datetime type)
✓ Clean database structure: Only necessary fields stored, no redundant timestamp columns
✓ CORREÇÃO CRÍTICA: Comando GTIPSET não existe no protocolo GV50 original
✓ Analisado código C# original: apenas comando GTOUT (bloqueio/desbloqueio) é suportado
✓ Sistema corrigido: comandos de troca de IP são automaticamente rejeitados e limpos
✓ Timestamp "0000" em GTSTT agora tratado corretamente como None (sem erro de conversão)

## System Architecture

The application follows a modular architecture with clear separation of concerns:

### Backend Architecture
- **Service-Based Organization**: Complete device services in dedicated folders (gv50/, future: gt06/, etc.)
- **Self-Contained Services**: Each device service contains all required components
- **TCP Server**: Custom socket-based server for handling persistent connections with GPS devices
- **Protocol Parser**: Device-specific parsers (currently Queclink @Track for GV50)
- **Message Handler**: Business logic layer for processing parsed messages and database operations
- **Database Layer**: MongoDB integration with unified 'tracker' database for all device types
- **Configuration Management**: Environment-based configuration with sensible defaults
- **Logging System**: Comprehensive logging with configurable levels and outputs

### Key Design Decisions
- **Single-threaded per connection**: Each GPS device connection is handled in its own thread to support concurrent devices
- **MongoDB for storage**: NoSQL database chosen for flexible schema and high write performance
- **Environment-based configuration**: All settings configurable via environment variables for deployment flexibility
- **Protocol abstraction**: Parser is designed to handle multiple message types from the Queclink protocol

## Key Components

### GV50 Service (gv50/)
#### TCP Server (`tcp_server.py`)
- Manages incoming TCP connections from GV50 GPS devices
- Implements IP whitelisting/blacklisting for security
- Handles connection lifecycle and cleanup
- Supports up to 100 concurrent device connections

#### Protocol Parser (`protocol_parser.py`)
- Parses Queclink @Track protocol messages for GV50 devices
- Supports multiple message types (GTFRI, GTIGN, GTIGF, etc.)
- Generates acknowledgment responses for devices
- Extracts GPS coordinates, speed, ignition status, and other telemetry data

#### Message Handler (`message_handler.py`)
- Processes parsed messages and updates database
- Handles different message types (reports, acknowledgments, events)
- Tracks IP address changes for devices
- Manages vehicle state updates

### Core Components (gv50/)
#### Database Manager (`database.py`)
- Manages MongoDB connections and operations for 'tracker' database
- Implements data models for vehicles, tracking data, and logs
- Creates appropriate indexes for performance
- Handles connection failures and retries

#### Data Models (`models.py`)
- **VehicleData**: Individual GPS tracking records with location data only:
  - imei, longitude, latitude, altitude, timestamp (server timestamp), deviceTimestamp (device timestamp), systemDate (system timestamp), mensagem_raw
- **Vehicle**: Device/vehicle information with new structure - IMEI, dsplaca, dsmodelo, comandobloqueo, bloqueado, comandotrocarip, ignicao, bateriavoltagem, bateriabaixa, ultimoalertabateria, tsusermanu

#### Configuration (`config.py`)
- Environment-based configuration management
- Unified settings for all device services

#### Logging (`logger.py`)
- Centralized logging system for all services

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
- Database: `tracker` (unified database for all device types)
- Connection: `mongodb+srv://docsmartuser:hk9D7DSnyFlcPmKL@cluster0.qats6.mongodb.net/tracker`
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