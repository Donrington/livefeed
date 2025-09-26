# Protobuf Setup and Compilation

## Installation

**Install protobuf compiler:**
```bash
# On Windows (using chocolatey or download from GitHub releases)
choco install protoc
# Or download protoc from https://github.com/protocolbuffers/protobuf/releases

# Install Python protobuf library
pip install protobuf
```

## Compilation

**Compile .proto files:**
```bash
# Basic syntax
protoc --python_out=. your_file.proto

# Example for this project
protoc --python_out=live_feed/app/ messages.proto
```

This generates the `messages_pb2.py` file from your `messages.proto` definition. Always ensure your protobuf compiler version matches the Python library version to avoid version mismatches.


## Troubleshooting

If you encounter version mismatch errors, upgrade protobuf:
```bash
pip install --upgrade protobuf
```