#!/usr/bin/env python3
"""
TCP Server for GV50 devices with long-lived connection support
Handles persistent TCP connections with proper keepalive and timeout management
Compatible with Windows (development) and Linux (production)
"""

import asyncio
import socket
import platform
from typing import Dict, Optional
from datetime import datetime, timedelta
from config import Config
from logger import logger

# Detect operating system
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'


class GV50TCPServer:
    """Asyncio TCP server with long-lived connection support"""
    
    def __init__(self):
        self.server: Optional[asyncio.Server] = None
        self.running = False
        self.connections: Dict[str, 'ClientConnection'] = {}
        self.message_handler = None
        self._cleanup_task = None
    
    async def start_server(self):
        """Start TCP server with automatic recovery from accept errors"""
        try:
            from message_handler import MessageHandler
            self.message_handler = MessageHandler()
            
            self.running = True
            
            # Set custom exception handler for asyncio loop (suppress WinError 64)
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(self._asyncio_exception_handler)
            
            # Start connection cleanup task
            self._cleanup_task = asyncio.create_task(self._connection_cleanup_loop())
            
            logger.info(f"TCP Server starting on {Config.SERVER_IP}:{Config.SERVER_PORT}")
            
            # Keep server running with automatic restart on errors
            while self.running:
                try:
                    await self._run_server()
                except Exception as e:
                    if self.running:
                        logger.error(f"Server error: {e}, restarting in 2 seconds...")
                        await asyncio.sleep(2)
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Fatal error starting TCP server: {e}")
            self.running = False
            raise
    
    async def _run_server(self):
        """Run server instance with proper error handling"""
        # Configure server - Windows doesn't support reuse_port
        import platform
        server_kwargs = {
            'reuse_address': True,
            'backlog': Config.MAX_CONNECTIONS
        }
        
        # Only add reuse_port on Linux
        if platform.system() == 'Linux':
            server_kwargs['reuse_port'] = True
        
        self.server = await asyncio.start_server(
            self.handle_client,
            Config.SERVER_IP,
            Config.SERVER_PORT,
            **server_kwargs
        )
        
        logger.info(f"TCP Server ready on {Config.SERVER_IP}:{Config.SERVER_PORT}")
        
        async with self.server:
            await self.server.serve_forever()
    
    def _asyncio_exception_handler(self, loop, context):
        """Custom exception handler for asyncio to suppress common Windows errors and keep server running"""
        exception = context.get('exception')
        message = context.get('message', '')
        
        # Suppress common Windows disconnection errors that are normal
        if isinstance(exception, OSError):
            if hasattr(exception, 'winerror') and exception.winerror in [64, 10054]:
                # WinError 64: Network name no longer available
                # WinError 10054: Connection reset by peer
                # These are normal when devices disconnect - suppress completely
                return
        
        # Suppress "Accept failed on a socket" messages for WinError 64
        if 'Accept failed on a socket' in message:
            if exception and isinstance(exception, OSError):
                if hasattr(exception, 'winerror') and exception.winerror == 64:
                    # This is a normal Windows disconnect - suppress
                    return
        
        # Suppress "Task exception was never retrieved" for these errors
        if exception and isinstance(exception, OSError):
            if hasattr(exception, 'winerror') and exception.winerror in [64, 10054]:
                return
        
        # For other exceptions, log them but don't use default handler (which is noisy)
        if exception:
            logger.debug(f"Asyncio exception: {exception}")
        else:
            logger.debug(f"Asyncio event: {message}")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection with long-lived support and robust error handling"""
        client_addr = writer.get_extra_info('peername')
        client_ip = client_addr[0] if client_addr else 'unknown'
        
        # Check IP whitelist
        if not Config.is_ip_allowed(client_ip):
            logger.warning(f"Connection rejected from unauthorized IP: {client_ip}")
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            return
        
        connection = ClientConnection(reader, writer, client_ip, self.message_handler)
        
        try:
            # Configure socket for long-lived connections
            self._configure_socket_keepalive(writer)
            
            logger.info(f"New connection from {client_ip}")
            
            # Process messages from this client
            await connection.process_messages()
            
        except asyncio.TimeoutError:
            logger.debug(f"Connection timeout for {client_ip}")
        except asyncio.CancelledError:
            logger.debug(f"Connection cancelled for {client_ip}")
        except ConnectionResetError:
            logger.debug(f"Connection reset by {client_ip}")
        except ConnectionAbortedError:
            logger.debug(f"Connection aborted by {client_ip}")
        except OSError as e:
            # Handle Windows-specific errors gracefully
            if hasattr(e, 'winerror') and e.winerror in [10054, 64]:
                logger.debug(f"Network disconnect for {client_ip}")
            else:
                logger.error(f"OS error handling client {client_ip}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling client {client_ip}: {e}")
        finally:
            await connection.close()
            if connection.imei and connection.imei in self.connections:
                del self.connections[connection.imei]
            logger.debug(f"Connection cleanup completed for {client_ip}")
    
    def _configure_socket_keepalive(self, writer: asyncio.StreamWriter):
        """Configure TCP keepalive to maintain long-lived connections (Windows/Linux compatible)"""
        try:
            # Get the actual socket object
            transport = writer.transport
            sock = None
            
            # Try different methods to get the real socket
            if hasattr(transport, '_sock'):
                sock = transport._sock
            elif hasattr(transport, 'get_extra_info'):
                sock = transport.get_extra_info('socket')
            
            if not sock:
                logger.warning("Could not get socket for keepalive configuration")
                return
            
            # Enable TCP keepalive (works on both Windows and Linux)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            # Platform-specific keepalive configuration
            if IS_LINUX:
                # Linux: Fine-grained control
                if hasattr(socket, 'TCP_KEEPIDLE'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                if hasattr(socket, 'TCP_KEEPINTVL'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                if hasattr(socket, 'TCP_KEEPCNT'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
                logger.debug(f"Linux TCP keepalive configured: 60s idle, 10s interval, 6 probes")
            elif IS_WINDOWS:
                # Windows: Try to set keepalive via ioctl if available
                try:
                    if hasattr(sock, 'ioctl') and hasattr(socket, 'SIO_KEEPALIVE_VALS'):
                        # (on/off, keepalive time ms, keepalive interval ms)
                        sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60000, 10000))
                        logger.debug("Windows TCP keepalive configured via ioctl: 60s idle, 10s interval")
                    else:
                        # Fallback: just enable keepalive without advanced config
                        logger.debug("Windows TCP keepalive enabled (basic mode)")
                except (AttributeError, OSError) as e:
                    # Python 3.13+ may not support ioctl on TransportSocket
                    logger.debug(f"Windows keepalive advanced config not available: {e}")
            
            # Disable Nagle's algorithm for low latency (works on both)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Set socket buffer sizes (works on both)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            
        except Exception as e:
            logger.error(f"Error configuring socket: {e}")
    
    async def _connection_cleanup_loop(self):
        """Periodically clean up stale connections and check server health"""
        last_connection_count = 0
        no_activity_count = 0
        
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.now()
                stale_connections = []
                
                for imei, conn in self.connections.items():
                    if now - conn.last_activity > timedelta(seconds=Config.CONNECTION_TIMEOUT):
                        stale_connections.append(imei)
                
                for imei in stale_connections:
                    logger.warning(f"Closing stale connection for IMEI: {imei}")
                    conn = self.connections.pop(imei, None)
                    if conn:
                        await conn.close()
                
                # Health check: detect if server is frozen
                current_count = len(self.connections)
                
                # If we had connections but now have none for too long, server might be frozen
                if last_connection_count > 0 and current_count == 0:
                    no_activity_count += 1
                else:
                    no_activity_count = 0
                
                last_connection_count = current_count
                
                # If no activity for 5 minutes and server should be running, log warning
                if no_activity_count > 5 and self.running:
                    logger.warning(f"No connections for {no_activity_count} minutes - server may need restart")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")
    
    def get_connection_count(self) -> int:
        """Get active connection count"""
        return len(self.connections)
    
    def get_connected_devices(self) -> list:
        """Get list of connected devices with details"""
        devices = []
        for imei, conn in self.connections.items():
            devices.append({
                'imei': imei,
                'ip': conn.client_ip,
                'last_activity': conn.last_activity.isoformat(),
                'connected_since': conn.last_activity.isoformat()
            })
        return devices
    
    def is_device_connected(self, imei: str) -> bool:
        """Check if specific device is connected"""
        return imei in self.connections
    
    def get_device_info(self, imei: str) -> dict:
        """Get info about specific connected device"""
        if imei in self.connections:
            conn = self.connections[imei]
            return {
                'imei': imei,
                'ip': conn.client_ip,
                'last_activity': conn.last_activity.isoformat(),
                'connected': True
            }
        return {'imei': imei, 'connected': False}
    
    def is_server_running(self) -> bool:
        """Check if server is running and accepting connections"""
        return self.running and self.server is not None
    
    def stop_server(self):
        """Stop TCP server"""
        self.running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        if self.server:
            self.server.close()
            logger.info("TCP Server stopped")


class ClientConnection:
    """Represents a single client connection with long-lived support"""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, 
                 client_ip: str, message_handler):
        self.reader = reader
        self.writer = writer
        self.client_ip = client_ip
        self.message_handler = message_handler
        self.imei: Optional[str] = None
        self.last_activity = datetime.now()
        self.buffer = bytearray()
        self.max_buffer_size = 65536  # 64KB max buffer
    
    async def process_messages(self):
        """Process incoming messages with proper buffer management and error handling"""
        while True:
            try:
                # Read with timeout to prevent hanging
                data = await asyncio.wait_for(
                    self.reader.read(4096),
                    timeout=Config.CONNECTION_TIMEOUT
                )
                
                if not data:
                    # Connection closed by client gracefully
                    logger.debug(f"Connection closed gracefully by {self.client_ip}")
                    break
                
                self.last_activity = datetime.now()
                
                # Add to buffer
                self.buffer.extend(data)
                
                # Prevent buffer overflow
                if len(self.buffer) > self.max_buffer_size:
                    logger.warning(f"Buffer overflow for {self.client_ip}, clearing buffer")
                    self.buffer = bytearray()
                    continue
                
                # Process complete messages
                await self._process_buffer()
                
            except asyncio.TimeoutError:
                # Timeout is normal for long-lived connections with infrequent messages
                # Just update activity time and continue
                self.last_activity = datetime.now()
                continue
                
            except asyncio.CancelledError:
                logger.debug(f"Connection cancelled for {self.client_ip}")
                break
            
            except ConnectionResetError:
                # Connection reset by peer (common in Windows)
                logger.debug(f"Connection reset by peer: {self.client_ip}")
                break
            
            except ConnectionAbortedError:
                # Connection aborted (common in Windows)
                logger.debug(f"Connection aborted: {self.client_ip}")
                break
            
            except OSError as e:
                # Handle Windows-specific network errors
                if e.winerror in [10054, 64]:  # Connection reset, Network name no longer available
                    logger.debug(f"Network error for {self.client_ip}: {e}")
                    break
                else:
                    logger.error(f"OS error processing message from {self.client_ip}: {e}")
                    break
                
            except Exception as e:
                logger.error(f"Unexpected error processing message from {self.client_ip}: {e}")
                break
    
    async def _process_buffer(self):
        """Process messages in buffer"""
        try:
            # Convert buffer to string
            buffer_str = self.buffer.decode('utf-8', errors='ignore')
            
            # GV50 messages end with '$'
            while '$' in buffer_str:
                # Find message boundary
                end_idx = buffer_str.index('$')
                message = buffer_str[:end_idx + 1].strip()
                
                # Remove processed message from buffer
                bytes_to_remove = len(message.encode('utf-8'))
                self.buffer = self.buffer[bytes_to_remove:]
                buffer_str = buffer_str[end_idx + 1:]
                
                if message:
                    # Process the message
                    await self._handle_message(message)
            
        except Exception as e:
            logger.error(f"Error processing buffer: {e}")
            # Clear buffer on error to prevent corruption
            self.buffer = bytearray()
    
    async def _handle_message(self, message: str):
        """Handle a single complete message"""
        try:
            # Extract IMEI from message if not already set
            if not self.imei:
                self.imei = self._extract_imei(message)
            
            # Update last activity
            self.last_activity = datetime.now()
            
            # Process message through handler
            if self.message_handler:
                response = await self.message_handler.process_message(message, self.imei, self.client_ip)
                
                # Send response if any
                if response:
                    await self.send_response(response)
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _extract_imei(self, message: str) -> Optional[str]:
        """Extract IMEI from message"""
        try:
            # GV50 messages format: +TYPE:MSGID,PROTOCOL,IMEI,...
            if message.startswith('+'):
                parts = message.split(',')
                if len(parts) >= 3:
                    return parts[2].strip()
            return None
        except Exception:
            return None
    
    async def send_response(self, response: str):
        """Send response to device"""
        try:
            if not response.endswith('\r\n'):
                response += '\r\n'
            
            self.writer.write(response.encode('utf-8'))
            await self.writer.drain()
            
            logger.debug(f"Sent response to {self.client_ip}: {response.strip()}")
            
        except Exception as e:
            logger.error(f"Error sending response to {self.client_ip}: {e}")
    
    async def close(self):
        """Close connection gracefully"""
        try:
            if self.writer and not self.writer.is_closing():
                self.writer.close()
                await self.writer.wait_closed()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


# Global server instance
tcp_server = GV50TCPServer()