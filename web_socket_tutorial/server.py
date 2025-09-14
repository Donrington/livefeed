#!/usr/bin/env python

import asyncio
import messages_pb2
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
port = 8001

async def handler(websocket):
    cam_message = messages_pb2.CameraSettings(brightness=80, cameraName="raspi_cam")
    await websocket.send(cam_message.SerializeToString())
    try:
        async for message in websocket:
            print(f"Received: {message}")
    except ConnectionClosedOK:
        print("Client disconnected normally.")
    except ConnectionClosedError as e:
        print(f"Client disconnected with error: {e}")
    finally:
        print("Connection closed.")


async def main():
    async with serve(handler, "", 8001) as server:
        print(f"WebSocket server running at ws://localhost:{port}")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())