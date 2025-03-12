# winConnect (Windows Only)
Communication Client->Daemon via NamedPipe

## ToDo:

- [x] Add support for other header settings
- [ ] Add logging
- [x] Add support for safe closing
- [ ] Add support for multiple clients
- [ ] Particular client to client communication
- [ ] Add support for encryption

## Description

This is a simple client-server communication system for Windows. The client and server communicate via a named pipe. The client sends a message to the server, and the server responds with a message. The client and server can be run on the same machine or on different machines.

## Usage

You can find examples in the [examples](examples) directory.

### Server

The server is a daemon that listens for incoming messages from clients. The server can be run on the same machine as the client or on a different machine. To run the server, use the following command:

```python
from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')  # test - name of the pipe

for data in connector.listen():
    print(f"({type(data)}) {data=}")
    if data is None and connector.closed:
        break
    connector.send_data(data)
```

### Client

The client sends a message to the server and waits for a response. To run the client, use the following command:

```python
from winConnect import WinConnectClient

connector = WinConnectClient('test')

with connector as conn:
    while True:
        i = input(":> ")
        if i == "exit": break
        conn.send_data(i)
        print(conn.read_pipe())
```

[//]: # (## Installation)

[//]: # ()
[//]: # (To install the package, use the following command:)

[//]: # ()
[//]: # (```bash)

[//]: # (pip install winConnect)

[//]: # (```)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
