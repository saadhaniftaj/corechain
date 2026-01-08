"""
WebSocket Server for Real-time Dashboard Updates
"""

import asyncio
import websockets
import json
from loguru import logger
from typing import Set
import os


class WebSocketServer:
    """WebSocket server for broadcasting real-time updates"""
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        
        logger.info(f"WebSocket server initialized on port {self.port}")
    
    async def register(self, websocket):
        """Register a new client"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address} (total: {len(self.clients)})")
        
        # Send welcome message
        await websocket.send(json.dumps({
            'event': 'connected',
            'message': 'Connected to CoreChain WebSocket server'
        }))
    
    async def unregister(self, websocket):
        """Unregister a client"""
        self.clients.remove(websocket)
        logger.info(f"Client disconnected: {websocket.remote_address} (total: {len(self.clients)})")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        
        # Send to all clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.unregister(client)
        
        logger.debug(f"Broadcasted {message.get('event')} to {len(self.clients)} clients")
    
    async def handler(self, websocket, path):
        """Handle WebSocket connections"""
        await self.register(websocket)
        
        try:
            async for message in websocket:
                # Echo back for now (can add request handling later)
                logger.debug(f"Received message: {message}")
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on port {self.port}...")
        
        self.server = await websockets.serve(
            self.handler,
            "0.0.0.0",
            self.port
        )
        
        logger.success(f"WebSocket server running on ws://0.0.0.0:{self.port}")
        
        # Keep server running
        await asyncio.Future()  # Run forever
    
    def run(self):
        """Run the WebSocket server (blocking)"""
        asyncio.run(self.start())


# Global instance for use by other modules
_websocket_server = None


def get_websocket_server() -> WebSocketServer:
    """Get or create WebSocket server instance"""
    global _websocket_server
    if _websocket_server is None:
        port = int(os.getenv('WEBSOCKET_PORT', 8001))
        _websocket_server = WebSocketServer(port)
    return _websocket_server


if __name__ == "__main__":
    server = WebSocketServer()
    server.run()
