#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging

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
    logger.info("🚀 Starting Simple Robot Server...")
    
    # Start WebSocket server
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    logger.info("✅ Robot server running on ws://0.0.0.0:8765")
    
    # Keep running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped")
