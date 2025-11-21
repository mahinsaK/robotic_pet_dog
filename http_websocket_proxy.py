# http_websocket_proxy.py - HTTP to WebSocket proxy for ngrok
import asyncio
import websockets
import json
import time
from aiohttp import web, WSMsgType
import aiohttp_cors

class HTTPWebSocketProxy:
    def __init__(self, websocket_port=8765):
        self.websocket_port = websocket_port
        self.relay_server = None
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        # WebSocket endpoint for direct connections (local use)
        self.app.router.add_get('/ws', self.websocket_handler)
        # Serve the mobile control HTML
        self.app.router.add_get('/', self.serve_index)
        self.app.router.add_static('/', '/home/ubuntu/without_ros')
    
    async def serve_index(self, request):
        return web.FileResponse('/home/ubuntu/without_ros/robot_mobile_control_ngrok.html')
    
    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Connect to the local relay server
        try:
            relay_ws = await websockets.connect(f'ws://localhost:{self.websocket_port}')
            
            # Proxy messages between HTTP WebSocket and local WebSocket
            async def proxy_to_relay():
                async for message in ws:
                    if message.type == WSMsgType.TEXT:
                        await relay_ws.send(message.data)
                    elif message.type == WSMsgType.ERROR:
                        print(f'WebSocket error: {ws.exception()}')
                        break
            
            async def proxy_from_relay():
                try:
                    async for message in relay_ws:
                        await ws.send_str(message)
                except Exception as e:
                    print(f"Relay connection error: {e}")
            
            # Run both proxy directions
            await asyncio.gather(
                proxy_to_relay(),
                proxy_from_relay(),
                return_exceptions=True
            )
        
        except Exception as e:
            print(f"Failed to connect to relay server: {e}")
            await ws.send_str(json.dumps({
                "type": "error", 
                "message": f"Could not connect to robot relay server: {e}"
            }))
        
        finally:
            if 'relay_ws' in locals():
                await relay_ws.close()
        
        return ws

async def main():
    proxy = HTTPWebSocketProxy()
    
    # Setup CORS for cross-origin requests
    cors = aiohttp_cors.setup(proxy.app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Add CORS to all routes
    for route in list(proxy.app.router.routes()):
        cors.add(route)
    
    print("🌐 HTTP-WebSocket Proxy Server Starting...")
    print("=" * 50)
    print("🔗 Local access: http://localhost:8080/")
    print("🌍 After ngrok: Use ngrok URL in browser")
    print("🤖 Robot should connect to relay on port 8765")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    runner = web.AppRunner(proxy.app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    # Keep running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Proxy server stopped")
