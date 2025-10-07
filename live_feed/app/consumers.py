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
                await self.send_connection_status(cam_data.isConnected)
               
            except Exception as e:
                log.error(f"Error parsing protobuf: {e}")

        
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
 
