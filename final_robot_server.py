#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging
from websockets.exceptions import InvalidUpgrade
from websockets.server import WebSocketServerProtocol

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Robot commands - replace with your actual robot functions
def execute_robot_command(command):
    commands = {
        'stand': 'Robot standing up',
        'sit': 'Robot sitting down',
        'walk': 'Robot walking forward', 
        'backward': 'Robot walking backward',
        'left': 'Robot turning left',
        'right': 'Robot turning right',
        'distance': 'Distance: 42cm',
        'stop': 'Robot stopped',
        'q': 'Robot shutdown'
    }
    return commands.get(command.lower(), f'Unknown: {command}')

class RobotWebSocketProtocol(WebSocketServerProtocol):
    """Custom WebSocket protocol that handles HTTP requests gracefully"""
    
    def process_request(self, path, request_headers):
        """Override to handle HTTP requests gracefully"""
        try:
            return super().process_request(path, request_headers)
        except InvalidUpgrade:
            # If it's not a proper WebSocket request, return HTTP response
            logger.info("📡 Received HTTP request - responding with HTTP 200")
            return (200, [('Content-Type', 'text/plain')], b'Robot WebSocket Server is running\n')

async def handle_client(websocket, path):
    """Handle each WebSocket connection"""
    logger.info(f"🔗 New client connected from {websocket.remote_address}")
    
    try:
        # Send welcome message
        await websocket.send("✅ Connected to Robot!")
        
        # Handle messages
        async for message in websocket:
            logger.info(f"📨 Received: {message}")
            
            # Execute command
            result = execute_robot_command(message.strip())
            logger.info(f"🤖 Result: {result}")
            
            # Send response
            await websocket.send(result)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("❌ Client disconnected")
    except Exception as e:
        logger.error(f"💥 Error: {e}")

async def main():
    logger.info("🚀 Starting Robust Robot Server...")
    
    # Start WebSocket server with custom protocol
    server = await websockets.serve(
        handle_client, 
        "0.0.0.0", 
        8765,
        create_protocol=RobotWebSocketProtocol
    )
    logger.info("✅ Robust robot server running on ws://0.0.0.0:8765")
    logger.info("📡 Also handles HTTP requests gracefully")
    
    # Keep running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped")
