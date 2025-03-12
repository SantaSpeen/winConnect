from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')
connector.set_header_settings(">L")

for data in connector.listen():
    print(data)
    connector.send_data(data)
