import json
from channels.generic.websocket import AsyncWebsocketConsumer
from . import messages_pb2


class CameraSettingsConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_settings = {
            'brightness': 1080,
            'cameraName': "nextgen_camera"
        }

    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        print("WebSocket connected - Camera control ready")

        # Send initial camera settings
        await self.send_camera_settings()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming messages from web dashboard
        if text_data:
            try:
                data = json.loads(text_data)
                if data.get('type') == 'update_camera_settings':
                    # Update camera settings from dashboard
                    if 'brightness' in data:
                        self.current_settings['brightness'] = int(data['brightness'])
                    if 'cameraName' in data:
                        self.current_settings['cameraName'] = data['cameraName']

                    print(f"Updated camera settings: {self.current_settings}")

                    # Send updated settings to Pi (protobuf) and dashboard (JSON)
                    await self.send_camera_settings()

            except json.JSONDecodeError:
                print(f"Invalid JSON received: {text_data}")

        # Handle protobuf messages from Pi
        if bytes_data:
            try:
                # Parse protobuf message from Pi
                cam_message = messages_pb2.CameraSettings()
                cam_message.ParseFromString(bytes_data)
                print(f"Received protobuf from Pi: brightness={cam_message.brightness}, camera={cam_message.cameraName}")

                # Update current settings
                self.current_settings['brightness'] = cam_message.brightness
                self.current_settings['cameraName'] = cam_message.cameraName

                # Send updated settings to dashboard
                await self.send_dashboard_update()

            except Exception as e:
                print(f"Error parsing protobuf: {e}")

    async def send_camera_settings(self):
        """Send camera settings to both Pi (protobuf) and dashboard (JSON)"""

        # Create protobuf message for Pi
        cam_message = messages_pb2.CameraSettings(
            brightness=self.current_settings['brightness'],
            cameraName=self.current_settings['cameraName']
        )

        # Send protobuf to Pi
        await self.send(bytes_data=cam_message.SerializeToString())

        # Send JSON to dashboard
        await self.send_dashboard_update()

    async def send_dashboard_update(self):
        """Send JSON update to dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'camera_settings_update',
            'brightness': self.current_settings['brightness'],
            'cameraName': self.current_settings['cameraName'],
            'timestamp': self.get_timestamp()
        }))

    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")