#!/usr/bin/env python3

import asyncio
import websockets
import json

async def simple_handler(websocket, path):
    print(f"🔌 Client connected from {websocket.remote_address}")
    try:
        await websocket.send(json.dumps({"type": "status", "message": "Simple server connected"}))
        async for message in websocket:
            print(f"📨 Received: {message}")
            response = {"type": "response", "echo": message}
            await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        print("📱 Client disconnected")
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    print("🚀 Starting simple WebSocket test server...")
    print("🌐 WebSocket server: ws://0.0.0.0:8766")
    
    start_server = websockets.serve(simple_handler, "0.0.0.0", 8766)
    await start_server
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
