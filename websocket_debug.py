#!/usr/bin/env python3

import asyncio
import websockets
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def echo_server(websocket, path):
    """Simple echo server for debugging WebSocket connections"""
    logger.info(f"🔗 New connection from: {websocket.remote_address}")
    logger.info(f"📍 Path: {path}")
    
    try:
        async for message in websocket:
            logger.info(f"📨 Received: {message}")
            
            # Echo the message back
            response = f"Echo: {message}"
            await websocket.send(response)
            logger.info(f"📤 Sent: {response}")
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("❌ Connection closed")
    except Exception as e:
        logger.error(f"💥 Error: {e}")

async def main():
    logger.info("🚀 Starting WebSocket debug server on port 8766...")
    
    # Start the server
    server = await websockets.serve(echo_server, "0.0.0.0", 8766)
    
    logger.info("✅ WebSocket debug server running!")
    logger.info("🌐 Connect with: ws://localhost:8766")
    logger.info("🌐 Or: ws://10.236.10.48:8766")
    logger.info("🛑 Press Ctrl+C to stop")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
