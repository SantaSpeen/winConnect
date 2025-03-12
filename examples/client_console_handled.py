from winConnect import WinConnectClient

connector = WinConnectClient('test')

def console():
    conn = connector.connect()
    while True:
        i = input(":> ")
        if i == "exit":
            break
        conn.send_data(i)
        data = conn.read_pipe()
        print(f"({type(data)}) {data=}")
    conn.close()

if __name__ == '__main__':
    console()
