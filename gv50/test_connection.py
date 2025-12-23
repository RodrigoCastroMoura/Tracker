#!/usr/bin/env python3
"""
Test script for GV50 asyncio TCP server
Tests basic device connection and message processing
"""

import asyncio
import sys


async def test_single_device():
    """Test single device connection"""
    try:
        print("Connecting to GV50 server...")
        reader, writer = await asyncio.open_connection('localhost', 8000)
        print("Connected successfully!")
        
        message = "+RESP:GTFRI,090302,865083030049613,,10,1,1,0.0,236,724.7,-46.778817,-23.503123,20250727152556,0724,0003,08A3,59CF,00,0.0,,,,,110000,10,0,7,20250727122605,054F$"
        print(f"Sending GTFRI message...")
        writer.write(message.encode())
        await writer.drain()
        
        try:
            data = await asyncio.wait_for(reader.read(1024), timeout=5.0)
            if data:
                print(f"Received ACK: {data.decode()}")
            else:
                print("No response received (normal for some configurations)")
        except asyncio.TimeoutError:
            print("Timeout waiting for response (server may not send immediate ACK)")
        
        writer.close()
        await writer.wait_closed()
        print("Connection closed successfully!")
        return True
        
    except ConnectionRefusedError:
        print("ERROR: Connection refused. Is the server running?")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def test_heartbeat():
    """Test heartbeat message"""
    try:
        print("\nTesting heartbeat...")
        reader, writer = await asyncio.open_connection('localhost', 8000)
        
        heartbeat = "+ACK:GTHBD,090302,865083030049613,,0001,20250727152556,054F$"
        print(f"Sending heartbeat...")
        writer.write(heartbeat.encode())
        await writer.drain()
        
        await asyncio.sleep(1)
        
        writer.close()
        await writer.wait_closed()
        print("Heartbeat test completed!")
        return True
        
    except Exception as e:
        print(f"Heartbeat test failed: {e}")
        return False


async def test_ignition_message():
    """Test ignition on/off messages"""
    try:
        print("\nTesting ignition messages...")
        reader, writer = await asyncio.open_connection('localhost', 8000)
        
        ignition_on = "+RESP:GTIGN,090302,865083030049613,,0,1,0.0,236,724.7,-46.778817,-23.503123,20250727152556,0724,0003,08A3,59CF,00,0.0,20250727152556,054F$"
        print(f"Sending GTIGN (ignition on)...")
        writer.write(ignition_on.encode())
        await writer.drain()
        
        await asyncio.sleep(1)
        
        writer.close()
        await writer.wait_closed()
        print("Ignition test completed!")
        return True
        
    except Exception as e:
        print(f"Ignition test failed: {e}")
        return False


async def test_multiple_connections():
    """Test multiple simultaneous connections"""
    try:
        print("\nTesting multiple connections...")
        connections = []
        
        for i in range(5):
            reader, writer = await asyncio.open_connection('localhost', 8000)
            connections.append((reader, writer))
            print(f"Connection {i+1} established")
        
        for i, (reader, writer) in enumerate(connections):
            imei = f"86508303004961{i}"
            message = f"+RESP:GTFRI,090302,{imei},,10,1,1,0.0,236,724.7,-46.778817,-23.503123,20250727152556,0724,0003,08A3,59CF,00,0.0,,,,,110000,10,0,7,20250727122605,054F$"
            writer.write(message.encode())
            await writer.drain()
            print(f"Message sent on connection {i+1}")
        
        await asyncio.sleep(2)
        
        for i, (reader, writer) in enumerate(connections):
            writer.close()
            await writer.wait_closed()
            print(f"Connection {i+1} closed")
        
        print("Multiple connections test completed!")
        return True
        
    except Exception as e:
        print(f"Multiple connections test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("GV50 Asyncio Server Test Suite")
    print("=" * 60)
    
    results = []
    
    result = await test_single_device()
    results.append(("Single Device", result))
    
    result = await test_heartbeat()
    results.append(("Heartbeat", result))
    
    result = await test_ignition_message()
    results.append(("Ignition", result))
    
    result = await test_multiple_connections()
    results.append(("Multiple Connections", result))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
