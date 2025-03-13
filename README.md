# winConnect (Windows Only)
Communicate Client-Server via Windows NamedPipe

## ToDo:

- [x] Add support for sending and receiving data
- [x] Add support for other header settings
- [x] Add support for safe closing
- [x] Add logging
- [ ] Send data in chunks (if data is too large)
- [x] Add support for encryption
  - [x] simple (via char xor; and auto-pairing)
  - [ ] password (via AES and PBKDF2)
  - [ ] certificate  (via RSA)
- [ ] Add support for multiple clients


## Description

This is a simple client-server communication system for Windows. The client and server communicate via a named pipe. The client sends a message to the server, and the server responds with a message. The client and server can be run on the same machine or on different machines.

## Installation

To install the package, use the following command:

```bash

pip install winConnect

```

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
