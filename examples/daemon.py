from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')
connector.set_header_settings(">L", 32)

for data in connector.listen():
    print(data)
    connector.send_data(data)
