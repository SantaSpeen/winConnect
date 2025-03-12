from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')
# Set header settings
# see: https://docs.python.org/3.13/library/struct.html#format-characters
# Default: ">L"
# >L - Big-endian long integer (header_size: 4 bytes, max_size: 4294967295)
connector.set_header_settings(">L")

for data in connector.listen():
    print(f"({type(data)}) {data=}")
    if data is None and connector.closed:
        break
    connector.send_data(data)
