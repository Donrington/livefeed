# WebSocket tutorial

This example demonstrates how to set up communication between a client and server using WebSockets, with Google Protocol Buffers (protobuf) for defining and sending custom messages.
In this example, the server sends a protobuf-defined message containing the brightness level and camera name to the client, which then prints the received data.

## Installation
```bash
pip install websockets
```
Install [Protocol buffers](https://github.com/protocolbuffers/protobuf/releases)


## How to Compile Custom Message
```bash
<protoc.exe> --python_out=. messages.proto
```

## How to Run 
Run the server.py in one terminal and then client.py in another terminal, the custom brightnesss and camera name set the by the server should now the printed on the client console terminal


  The key changes are:
  - Replace response = await websocket.recv() with async for message in websocket:
  - Add the brightness application function
  - Add confirmation sending back to Django
  - Wrap everything in a reconnection loop