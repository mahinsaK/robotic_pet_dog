#!/usr/bin/env python3

import asyncio
import websockets
from websockets import serve, WebSocketServerProtocol
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import InvalidUpgrade
import json
import logging
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridRobotServer:
    """
    Hybrid server that handles both WebSocket and HTTP requests
    This solves the "invalid Connection header: keep-alive" issue
    """
    
    def __init__(self):
        self.clients = {}
        logger.info("🤖 Hybrid Robot Server initialized")

    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        client_id = f"client_{len(self.clients) + 1}_{websocket.remote_address[0]}"
        self.clients[client_id] = websocket
        logger.info(f"👥 Client registered: {client_id}")
        return client_id

    async def unregister_client(self, websocket):
        """Unregister a disconnected client"""
        client_id = None
        for cid, ws in self.clients.items():
            if ws == websocket:
                client_id = cid
                break
        
        if client_id:
            del self.clients[client_id]
            logger.info(f"👋 Client unregistered: {client_id}")
        
        logger.info(f"👥 Active clients: {len(self.clients)}")

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
            logger.info(f"📨 Received message: {message}")
            
            # Try to parse as JSON first (for structured messages)
            try:
                data = json.loads(message)
                
                if data.get('type') == 'command':
                    command = data.get('command', '').strip()
                    if command:
                        result = await self.execute_robot_command(command)
                        response = {
                            'type': 'response',
                            'command': command,
                            'result': result,
                            'timestamp': datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                
                elif data.get('type') == 'identify':
                    # Handle relay server identification
                    response = {
                        'type': 'identification_ack',
                        'client_type': 'robot',
                        'message': 'Robot server ready',
                        'timestamp': datetime.now().isoformat()
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

    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        client_id = await self.register_client(websocket)
        logger.info(f"🔗 WebSocket connected: {client_id} from {websocket.remote_address}")
        logger.info(f"📍 Path: {path}")
        
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
            logger.info(f"WebSocket connection closed: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            await self.unregister_client(websocket)

    def process_request(self, server, request):
        """
        Custom request processor to handle HTTP requests to WebSocket endpoint
        This prevents the "invalid Connection header: keep-alive" error
        """
        # Get headers from the request object
        request_headers = request.headers
        path = request.path
        
        # Check if this is a proper WebSocket upgrade request
        connection = request_headers.get("Connection", "").lower()
        upgrade = request_headers.get("Upgrade", "").lower()
        
        logger.info(f"📥 Request to {path}")
        logger.info(f"🔍 Connection: {connection}")
        logger.info(f"🔍 Upgrade: {upgrade}")
        
        # If it's not a WebSocket upgrade request, return HTTP response
        if "upgrade" not in connection or upgrade != "websocket":
            logger.info("🌐 HTTP request detected, returning status response")
            
            # Return a simple HTTP response
            status_response = {
                "status": "ok",
                "message": "Robot WebSocket Server is running",
                "endpoint": f"ws://{request_headers.get('Host', 'localhost')}/",
                "available_commands": ["stand", "sit", "walk", "backward", "left", "right", "distance", "stop"],
                "timestamp": datetime.now().isoformat()
            }
            
            response_body = json.dumps(status_response, indent=2)
            
            return (
                200,  # HTTP status code
                [("Content-Type", "application/json"), ("Access-Control-Allow-Origin", "*")],
                response_body.encode()
            )
        
        # Let WebSocket handle the upgrade
        return None

    async def start_server(self, host="0.0.0.0", port=8765):
        """Start the hybrid server"""
        logger.info("🚀 Starting Hybrid Robot Server")
        logger.info(f"🌐 Server URL: ws://{host}:{port}")
        logger.info("📋 Supported commands: stand, sit, walk, backward, left, right, distance, stop")
        logger.info("🔗 Handles both WebSocket and HTTP requests")
        logger.info("=" * 50)
        
        # Create server with custom request processor
        server = await serve(
            self.websocket_handler,
            host,
            port,
            process_request=self.process_request
        )
        
        logger.info(f"✅ Hybrid server is ready for connections!")
        return server

async def main():
    """Main function to start the hybrid server"""
    try:
        server = HybridRobotServer()
        websocket_server = await server.start_server()
        
        # Keep the server running
        await websocket_server.wait_closed()
        
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
