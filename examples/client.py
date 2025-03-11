from winConnect import WinConnectClient

connector = WinConnectClient('test')

for data in connector.listen():
    print(data)
    i = input(":> ")
    connector.send_data(i)
