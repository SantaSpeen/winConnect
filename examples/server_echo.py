from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')
# Set header settings
# see: https://docs.python.org/3.13/library/struct.html#format-characters
# Default: ">H" - Big-endian unsigned short integer (header_size: 2 bytes, max_size: 65535)
connector.set_header_settings(">H")

for data in connector.listen():
    print(f"({type(data)}) {data=}")
    if data is None and connector.closed:
        break
    connector.send_data(data)
