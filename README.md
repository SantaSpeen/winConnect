# winConnect (Windows Only)
Communication Client->Daemon via NamedPipe

## Description

This is a simple client-server communication system for Windows. The client and server communicate via a named pipe. The client sends a message to the server, and the server responds with a message. The client and server can be run on the same machine or on different machines.

## Usage

### Server

The server is a daemon that listens for incoming messages from clients. The server can be run on the same machine as the client or on a different machine. To run the server, use the following command:

```python
from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')
connector.set_header_settings(">L", 32)

for data in connector.listen():
    print(data)
    connector.send_data(data)
```

### Client

The client sends a message to the server and waits for a response. To run the client, use the following command:

```python
from winConnect import WinConnectClient

connector = WinConnectClient('test')

for data in connector.listen():
    print(data)
    i = input(":> ")
    connector.send_data(i)
```

## Installation

To install the package, use the following command:

```bash
pip install winConnect
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
