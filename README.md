# GPS Tracker Service

A comprehensive Python-based GPS tracking service designed for multiple device types with modular architecture.

## Project Structure

```
├── .env                       # Environment configuration (root)
├── deps.txt                   # Python dependencies
├── gv50/                      # Complete GV50 service
│   ├── main.py               # Main service entry point
│   ├── config.py             # Configuration management
│   ├── database.py           # MongoDB database manager
│   ├── logger.py             # Logging system
│   ├── models.py             # Data models
│   ├── tcp_server.py         # TCP server for GV50
│   ├── protocol_parser.py    # Queclink @Track protocol parser
│   └── message_handler.py    # Message processing logic
└── logs/                     # Application logs
```

## Features

- **Multi-Device Support**: Modular architecture ready for additional device types
- **GV50 Support**: Complete Queclink @Track protocol implementation
- **MongoDB Integration**: Unified 'tracker' database with 2 tables (vehicle_data, vehicles)
- **Real-time Processing**: TCP server with concurrent connection support
- **Comprehensive Logging**: Configurable logging system
- **IP Management**: Configurable allowed IPs for security

## Current Device Support

### GV50 GPS Tracker
- **Protocol**: Queclink @Track V4.01
- **Message Types**: GTFRI (location), GTIGN/GTIGF (ignition), GTOUT (control)
- **Port**: 5000 (TCP)
- **Features**: Real-time tracking, ignition detection, acknowledgment responses

## Database Schema

### vehicle_data (10 fields)
- `imei`: Device identifier
- `longitude`, `latitude`, `altitude`: GPS coordinates
- `speed`: Vehicle speed
- `ignition`: Ignition status
- `battery_level`: Device battery level
- `timestamp`: Server timestamp
- `deviceTimestamp`: Device timestamp
- `systemDate`: System timestamp
- `mensagem_raw`: Raw message data

### vehicles
- Device/vehicle information and current status

## Installation

### Using Git (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd gps-tracker-service
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r deps.txt
   ```

3. **Configure environment variables:**
   ```bash
   nano .env  # Edit configuration file in root directory
   ```

4. **Run the service:**
   ```bash
   cd gv50 && python main.py
   ```

### Manual Installation

1. **Download and extract the source code**
2. **Install dependencies:**
   ```bash
   pip install -r deps.txt
   ```
   Or manually:
   ```bash
   pip install pymongo python-dotenv
   ```
3. **Configure the `.env` file in root directory with your settings**
4. **Run the service from the `gv50/` directory**

## Updates

### Updating via Git

1. **Stop the running service:**
   ```bash
   # Stop the service (Ctrl+C if running manually)
   # Or if using systemd: sudo systemctl stop gv50-tracker.service
   ```

2. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

3. **Update dependencies if needed:**
   ```bash
   pip install --upgrade pymongo python-dotenv
   ```

4. **Restart the service:**
   ```bash
   cd gv50
   python main.py
   # Or if using systemd: sudo systemctl start gv50-tracker.service
   ```

### Manual Update

1. **Backup your configuration:**
   ```bash
   cp .env .env.backup
   ```

2. **Download and extract new version**
3. **Restore your configuration:**
   ```bash
   cp .env.backup .env
   ```
4. **Restart the service**

## Quick Start

1. Configure environment variables (IPs, logging)
2. Run: `python main.py`
3. Service listens on port 5000 for GV50 devices

## Adding New Device Types

1. Create new service folder: `new_device/` (e.g., `gt06/`, `tk103/`)
2. Copy complete service structure from `gv50/`
3. Implement device-specific protocol parser
4. Adapt TCP server for device protocol  
5. Update message handler for device data format
6. Update main.py to include new service

The modular architecture ensures easy addition of new GPS tracker device types.