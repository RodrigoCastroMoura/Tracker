#!/usr/bin/env python3
"""
GV50 Service Starter - Asyncio Version
"""
import os
import sys
import asyncio

os.environ['SERVER_PORT'] = '8000'
os.environ['DATABASE_NAME'] = 'tracker'

from main import GV50TrackerService


async def run_service():
    """Run GV50 service with asyncio"""
    print("=== STARTING GV50 SERVICE ON PORT 8000 (Asyncio) ===")
    
    service = GV50TrackerService()
    
    try:
        await service.start()
        print("GV50 Service started successfully on port 8000")
        
    except KeyboardInterrupt:
        print("\nService interrupted by user")
    except Exception as e:
        print(f"Service error: {e}")
    finally:
        service.stop()


def main():
    """Main entry point"""
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        sys.exit(0)


if __name__ == "__main__":
    main()
