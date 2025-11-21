#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobotServer:
    def __init__(self):
        self.clients = set()
        
    def execute_command(self, command):
        """Execute robot command - replace with actual robot code"""
        commands = {
            'stand': '🧍 Robot standing up',
            'sit': '🪑 Robot sitting down',
            'walk': '🚶 Robot walking forward', 
            'backward': '🔙 Robot walking backward',
            'left': '⬅️ Robot turning left',
            'right': '➡️ Robot turning right',
            'distance': '📏 Distance sensor: 42cm',
            'stop': '🛑 Robot emergency stop',
            'q': '🔴 Robot shutdown'
        }
        return commands.get(command.lower(), f'❓ Unknown command: {command}')
    
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections with error recovery"""
        client_addr = websocket.remote_address
        logger.info(f"🔗 WebSocket client connected: {client_addr}")
        self.clients.add(websocket)
        
        try:
            # Send welcome message
            await websocket.send("✅ Connected to Robot Server!")
            
            # Handle messages
            async for message in websocket:
                logger.info(f"📨 Command from {client_addr}: {message}")
                
                # Execute command
                result = self.execute_command(message.strip())
                logger.info(f"🤖 Response: {result}")
                
                # Send response
                await websocket.send(result)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"❌ WebSocket client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"💥 WebSocket error for {client_addr}: {e}")
        finally:
            self.clients.discard(websocket)

class DualProtocolServer:
    """A server that handles both HTTP and WebSocket on different ports"""
    
    def __init__(self):
        self.robot_server = RobotServer()
        
    def start_http_server(self, port=8080):
        """Start HTTP server in a separate thread"""
        def run_http():
            try:
                server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
                logger.info(f"🌐 HTTP server started on port {port}")
                server.serve_forever()
            except Exception as e:
                logger.error(f"💥 HTTP server error: {e}")
        
        thread = threading.Thread(target=run_http, daemon=True)
        thread.start()
        return thread
    
    async def start_websocket_server(self, port=8765):
        """Start WebSocket server with error handling"""
        try:
            # Create WebSocket server with proper error handling
            logger.info(f"🚀 Starting WebSocket server on port {port}...")
            
            async def safe_handler(websocket, path):
                try:
                    await self.robot_server.handle_websocket(websocket, path)
                except Exception as e:
                    logger.error(f"Handler error: {e}")
            
            server = await websockets.serve(
                safe_handler,
                "0.0.0.0", 
                port,
                ping_interval=20,
                ping_timeout=10,
                compression=None
            )
            
            logger.info(f"✅ WebSocket server running on ws://0.0.0.0:{port}")
            return server
            
        except Exception as e:
            logger.error(f"💥 Failed to start WebSocket server: {e}")
            raise

async def main():
    logger.info("🤖 Starting Dual Protocol Robot Server...")
    
    # Create server instance
    server = DualProtocolServer()
    
    # Start HTTP server for web pages
    server.start_http_server(8080)
    
    # Start WebSocket server for robot commands
    ws_server = await server.start_websocket_server(8765)
    
    logger.info("")
    logger.info("🎉 ROBOT CONTROL SYSTEM READY!")
    logger.info("=" * 40)
    logger.info("🌐 Web Interface: http://localhost:8080/easy_robot_control.html")
    logger.info("🤖 WebSocket: ws://localhost:8765")
    logger.info("🌍 Network: http://10.236.10.48:8080/easy_robot_control.html")
    logger.info("🛑 Press Ctrl+C to stop")
    logger.info("=" * 40)
    logger.info("")
    
    # Keep running
    await ws_server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
