#!/usr/bin/env python3
"""
Enhanced Robot WebSocket Server with Relay Support
Handles both direct connections and relay server architecture
"""

import asyncio
import websockets
import json
import time
import logging
import signal
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobotServer:
    def __init__(self):
        self.clients = set()
        self.running = True
        logger.info("🤖 Robot WebSocket Server initialized")

    async def register_client(self, websocket):
        """Register a new client"""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"📱 Client connected from {client_addr[0]}:{client_addr[1]}")

    async def unregister_client(self, websocket):
        """Unregister a client"""
        self.clients.discard(websocket)
        logger.info(f"📱 Client disconnected")

    async def broadcast_message(self, message, exclude=None):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        failed_clients = []
        for client in list(self.clients):
            if client == exclude:
                continue
            try:
                await client.send(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                failed_clients.append(client)
        
        # Clean up failed clients
        for client in failed_clients:
            self.clients.discard(client)

    async def execute_robot_command(self, command):
        """Execute robot command - MOCK IMPLEMENTATION"""
        logger.info(f"🤖 Executing command: {command}")
        
        # Mock robot responses - Replace with your actual robot code
        responses = {
            'stand': 'Robot standing up',
            'sit': 'Robot sitting down', 
            'walk': 'Robot walking forward with obstacle avoidance',
            'backward': 'Robot walking backward',
            'left': 'Robot turning left',
            'right': 'Robot turning right',
            'distance': f'Distance sensor reading: {42.5} cm',
            'stop': 'Emergency stop activated - robot stopped',
            'q': 'Robot shutdown sequence initiated'
        }
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        return responses.get(command.lower(), f'Unknown command: {command}')

    async def handle_client_message(self, websocket, message):
        """Handle incoming messages from clients"""
        try:
            # Try to parse as JSON first (relay server format)
            try:
                data = json.loads(message)
                if data.get('type') == 'robot_command':
                    command = data.get('command', '')
                    result = await self.execute_robot_command(command)
                    
                    response = {
                        'type': 'response',
                        'command': command,
                        'message': result,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                        'success': True
                    }
                    await websocket.send(json.dumps(response))
                    
                elif data.get('type') == 'ping':
                    pong_response = {
                        'type': 'pong',
                        'timestamp': time.time()
                    }
                    await websocket.send(json.dumps(pong_response))
                    
                else:
                    logger.warning(f"Unknown message type: {data.get('type')}")
                    
            except json.JSONDecodeError:
                # Handle plain text commands (direct connection)
                command = message.strip()
                result = await self.execute_robot_command(command)
                await websocket.send(result)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            error_response = f"Error: {str(e)}"
            try:
                await websocket.send(error_response)
            except:
                pass

    async def client_handler(self, websocket, path):
        """Handle WebSocket client connections"""
        await self.register_client(websocket)
        
        try:
            # Send welcome message
            welcome_msg = {
                'type': 'welcome',
                'message': 'Connected to SpotMicro Robot',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'available_commands': ['stand', 'sit', 'walk', 'backward', 'left', 'right', 'distance', 'stop']
            }
            await websocket.send(json.dumps(welcome_msg))
            
            async for message in websocket:
                await self.handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            await self.unregister_client(websocket)

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down robot server...")
        self.running = False
        
        # Notify all clients
        shutdown_msg = {
            'type': 'server_shutdown',
            'message': 'Robot server shutting down',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        }
        await self.broadcast_message(json.dumps(shutdown_msg))

# Global server instance
robot_server = RobotServer()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    asyncio.create_task(robot_server.shutdown())

async def start_server():
    """Start the WebSocket server"""
    host = "0.0.0.0"
    port = 8765
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting Robot WebSocket Server")
    logger.info(f"🌐 Server URL: ws://{host}:{port}")
    logger.info("📋 Supported commands: stand, sit, walk, backward, left, right, distance, stop")
    logger.info("🔗 Compatible with both direct connections and relay servers")
    logger.info("=" * 60)
    
    try:
        async with websockets.serve(
            robot_server.client_handler,
            host,
            port,
            ping_interval=20,
            ping_timeout=10
        ):
            logger.info("✅ Robot server is ready for connections!")
            await asyncio.Future()  # Run forever
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("\n🛑 Server shutdown completed")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
