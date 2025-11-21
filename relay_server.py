# relay_server.py
import asyncio
import websockets
import json
import time

class RelayServer:
    def __init__(self):
        self.robot_client = None
        self.controller_clients = set()

    async def register(self, websocket, client_type):
        if client_type == 'robot':
            if self.robot_client:
                await websocket.send(json.dumps({"type": "error", "message": "Robot already connected"}))
                return False
            self.robot_client = websocket
            print(f"🤖 Robot connected at {time.strftime('%H:%M:%S')}")
        elif client_type == 'controller':
            self.controller_clients.add(websocket)
            print(f"📱 Controller connected at {time.strftime('%H:%M:%S')} (Total controllers: {len(self.controller_clients)})")
        else:
            await websocket.send(json.dumps({"type": "error", "message": "Unknown client type"}))
            return False
        return True

    async def unregister(self, websocket):
        if websocket == self.robot_client:
            self.robot_client = None
            print(f"🤖 Robot disconnected at {time.strftime('%H:%M:%S')}")
        if websocket in self.controller_clients:
            self.controller_clients.discard(websocket)
            print(f"📱 Controller disconnected at {time.strftime('%H:%M:%S')} (Remaining: {len(self.controller_clients)})")

    async def relay_to_robot(self, message):
        if self.robot_client:
            try:
                await self.robot_client.send(message)
                print(f"📤 Relayed command to robot: {json.loads(message).get('command', 'unknown')}")
            except Exception as e:
                print(f"❌ Failed to relay to robot: {e}")
                self.robot_client = None

    async def relay_to_controllers(self, message):
        if self.controller_clients:
            dead_clients = []
            for client in self.controller_clients:
                try:
                    await client.send(message)
                except:
                    dead_clients.append(client)
            
            # Remove dead clients
            for client in dead_clients:
                self.controller_clients.discard(client)
            
            if dead_clients:
                print(f"🧹 Cleaned up {len(dead_clients)} dead controller connections")

    async def handler(self, websocket, path=None):
        try:
            # First message must be identification
            message = await websocket.recv()
            data = json.loads(message)
            
            if data.get('type') != 'identify':
                await websocket.send(json.dumps({"type": "error", "message": "First message must be identification"}))
                await websocket.close()
                return
                
            client_type = data.get('client_type')
            if not await self.register(websocket, client_type):
                await websocket.close()
                return

            # Send welcome message
            if client_type == 'controller':
                status = "Robot connected" if self.robot_client else "Robot not connected"
                await websocket.send(json.dumps({
                    "type": "status", 
                    "message": f"Connected to relay server. {status}."
                }))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if client_type == 'controller' and data.get('type') == 'robot_command':
                        # Relay command to robot
                        if self.robot_client:
                            await self.relay_to_robot(message)
                        else:
                            await websocket.send(json.dumps({
                                "type": "error", 
                                "message": "Robot is not connected to relay server"
                            }))
                            
                    elif client_type == 'robot' and data.get('type') in ['status', 'response', 'error']:
                        # Relay status/response to controllers
                        await self.relay_to_controllers(message)
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error", 
                        "message": "Invalid JSON message"
                    }))
                except Exception as e:
                    print(f"❌ Handler error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"❌ Connection error: {e}")
        finally:
            await self.unregister(websocket)

async def main():
    relay = RelayServer()
    print("🌐 Starting Relay WebSocket Server")
    print("=" * 50)
    print("Server running on ws://0.0.0.0:8765")
    print("🤖 Robots should connect as client_type: 'robot'")
    print("📱 Controllers should connect as client_type: 'controller'")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    async with websockets.serve(relay.handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Relay server stopped")
