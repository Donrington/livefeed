import json
from channels.generic.websocket import AsyncWebsocketConsumer
from messages import messages_pb2
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s"
)
log = logging.getLogger(__name__) 

class CameraSettingsConsumer(AsyncWebsocketConsumer):
    group_name = "camera_group"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        log.info("WebSocket connected - Camera control ready")
                
    async def disconnect(self, close_code):
        log.info(f"WebSocket disconnected with code: {close_code}")
        await self.channel_layer.group_add(self.group_name, self.channel_name)


    async def connection_status(self, event):
        if event.get("origin") == self.channel_name: #exclude the sender of the message 
            return

        isConnected = event['isConnected']
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'isConnected': isConnected,
        }))

    async def receive(self, text_data=None, bytes_data=None):
        # Handle protobuf messages from Pi
        if bytes_data:
            try:
                cam_data = messages_pb2.CameraStatus()
                cam_data.ParseFromString(bytes_data)

                # Send camera status including settings to frontend
                await self.send_camera_status(cam_data)

            except Exception as e:
                log.error(f"Error parsing protobuf: {e}")

        # Handle JSON messages from JavaScript (setting change commands)
        if text_data:
            try:
                data = json.loads(text_data)
                message_type = data.get('type')

                if message_type == 'camera_setting':
                    # Forward camera setting command to Pi
                    setting = data.get('setting')
                    value = data.get('value')
                    await self.send_setting_to_pi(setting, value)

            except Exception as e:
                log.error(f"Error handling JSON message: {e}")

        
    async def send_camera_status(self, cam_data):
        """Send complete camera status including settings to frontend"""
        await self.send(text_data=json.dumps({
            'type': 'camera_status',
            'isConnected': cam_data.isConnected,
            'brightness': cam_data.brightness,
            'contrast': cam_data.contrast,
            'exposure': cam_data.exposure,  # Already multiplied by 10 from Pi
            'focus': cam_data.focus,
        }))
        log.info(f"Sent camera status to frontend: brightness={cam_data.brightness}, contrast={cam_data.contrast}")

    async def send_setting_to_pi(self, setting: str, value: int):
        """Send camera setting command to Pi via protobuf"""
        try:
            # Create protobuf command message
            cmd = messages_pb2.CameraSettingsCommand()
            cmd.setting = setting
            cmd.value = value

            # Send binary protobuf message to Pi
            await self.send(bytes_data=cmd.SerializeToString())
            log.info(f"Sent setting command to Pi: {setting} = {value}")

        except Exception as e:
            log.error(f"Error sending setting to Pi: {e}")

    async def send_connection_status(self, connected: bool):
        """Send connection status to dashboard"""
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'connection_status',
                'isConnected': connected,
                "origin": self.channel_name,
            }
        )

