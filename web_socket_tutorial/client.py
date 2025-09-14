import asyncio
import websockets
import messages_pb2
port = 8001



async def websocket_client():
    uri = f"ws://localhost:{port}"  # Replace with your WebSocket server address
    cam_message = messages_pb2.CameraSettings()
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")
        response = await websocket.recv()
        cam_message.ParseFromString(response)
        print(f"Received: brightness setting of  {cam_message.brightness} for {cam_message.cameraName}")

asyncio.run(websocket_client())
