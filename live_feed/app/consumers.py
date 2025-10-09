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
        self.is_pi_connection = False  # Track if this is Pi or browser

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
                # Mark this connection as coming from Pi
                self.is_pi_connection = True

                cam_data = messages_pb2.CameraStatus()
                cam_data.ParseFromString(bytes_data)

                # Send camera status to ALL browser clients (but not back to Pi)
                await self.broadcast_camera_status(cam_data)

            except Exception as e:
                log.error(f"Error parsing protobuf: {e}")

        # Handle JSON messages from JavaScript (setting change commands)
        if text_data:
            try:
                data = json.loads(text_data)
                message_type = data.get('type')

                if message_type == 'camera_setting':
                    # Forward camera setting command to Pi only
                    setting = data.get('setting')
                    value = data.get('value')
                    await self.send_setting_to_pi(setting, value)

            except Exception as e:
                log.error(f"Error handling JSON message: {e}")

        
    async def broadcast_camera_status(self, cam_data):
        """Broadcast camera status to all browser clients via channel layer"""
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'camera_status_update',
                'isConnected': cam_data.isConnected,
                'brightness': cam_data.brightness,
                'fps': cam_data.fps,
            }
        )
        log.info(f"Broadcast camera status: brightness={cam_data.brightness}, fps={cam_data.fps:.1f}")

    async def camera_status_update(self, event):
        """Handler for camera_status_update group messages - sends JSON to browser"""
        # Only send to browser clients, not to Pi
        if not self.is_pi_connection:
            await self.send(text_data=json.dumps({
                'type': 'camera_status',
                'isConnected': event['isConnected'],
                'brightness': event['brightness'],
                'fps': event['fps'],
            }))

    async def send_setting_to_pi(self, setting: str, value: int):
        """Send camera setting command to Pi via channel layer"""
        try:
            # Broadcast to all connections
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'forward_setting_to_pi',
                    'setting': setting,
                    'value': value,
                }
            )
            log.info(f"Broadcasting setting command: {setting} = {value}")

        except Exception as e:
            log.error(f"Error sending setting to Pi: {e}")

    async def forward_setting_to_pi(self, event):
        """Handler for forward_setting_to_pi - sends protobuf to Pi only"""
        # Only send to Pi connection, not to browsers
        if self.is_pi_connection:
            try:
                cmd = messages_pb2.CameraSettingsCommand()
                cmd.setting = event['setting']
                cmd.value = event['value']

                await self.send(bytes_data=cmd.SerializeToString())
                log.info(f"Forwarded to Pi: {event['setting']} = {event['value']}")

            except Exception as e:
                log.error(f"Error forwarding to Pi: {e}")

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

