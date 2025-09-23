# import asyncio
# import websockets
# import messages_pb2
# port = 9000



# async def websocket_client():
#     uri = f"ws://10.9.0.1:{port}/ws/camera/"  # Replace with your WebSocket server address
#     cam_message = messages_pb2.CameraSettings()
#     async with websockets.connect(uri) as websocket:
#         print("Connected to WebSocket server")
#         response = await websocket.recv()
#         cam_message.ParseFromString(response)
#         print(f"Received: brightness setting of  {cam_message.brightness} for {cam_message.cameraName}")

# asyncio.run(websocket_client())




import asyncio
import websockets
import messages_pb2

port = 9000  # ← CHANGE THIS! Your server is running on 9001, not 9000

def apply_camera_brightness(brightness_value):
    """Simulate camera brightness - no actual camera needed"""
    print(f"[SIMULATED] Applied brightness: {brightness_value}")

async def websocket_client():
    uri = f"ws://10.9.0.1:{port}/ws/camera/"

    while True:
        try:
            print(f"🔗 Connecting to {uri}...")
            async with websockets.connect(uri) as websocket:
                print("✅ Connected to WebSocket server")

                async for message in websocket:
                    try:
                        # Try to parse as protobuf bytes first
                        if isinstance(message, bytes):
                            cam_message = messages_pb2.CameraSettings()
                            cam_message.ParseFromString(message)
                            print(f"📨 Received PROTOBUF: brightness={cam_message.brightness} for {cam_message.cameraName}")

                            apply_camera_brightness(cam_message.brightness)

                            # Send confirmation back
                            confirmation = messages_pb2.CameraSettings()
                            confirmation.brightness = cam_message.brightness
                            confirmation.cameraName = "pi_camera_confirmed"
                            await websocket.send(confirmation.SerializeToString())
                            print(f"✅ Sent confirmation back")

                        elif isinstance(message, str):
                            # Handle text messages (JSON from Django)
                            print(f"📨 Received JSON: {message}")
                            # Optionally parse JSON if needed

                        else:
                            print(f"⚠️ Unknown message type: {type(message)}")

                    except Exception as e:
                        print(f"❌ Error processing message: {e}")
                        print(f"   Message type: {type(message)}")
                        print(f"   Message content: {message}")
                        continue

        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

asyncio.run(websocket_client())