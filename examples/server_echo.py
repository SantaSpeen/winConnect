from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')

for data in connector.listen():
    print(f"({type(data)}) {data=}")
    if data is None and connector.closed:
        break
    connector.send_data(data)
