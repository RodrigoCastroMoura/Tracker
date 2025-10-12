#!/usr/bin/env python3
"""
GV50 Service Starter - Force correct configuration
"""
import os
import sys

# Force correct configuration before importing other modules
os.environ['SERVER_PORT'] = '8000'  # GV50 devices connect on port 8000
os.environ['DATABASE_NAME'] = 'tracker'  # Use correct database

# Now import and start the service
from main import GV50TrackerService

def main():
    """Start GV50 service with correct configuration"""
    print("=== STARTING GV50 SERVICE ON PORT 8000 ===")
    
    service = GV50TrackerService()
    
    try:
        if service.start():
            print("✅ GV50 Service started successfully on port 8000")
            # Keep service running
            while service.running:
                import time
                time.sleep(1)
        else:
            print("❌ Failed to start GV50 service")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Service interrupted by user")
        service.stop()
    except Exception as e:
        print(f"❌ Service error: {e}")
        service.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()