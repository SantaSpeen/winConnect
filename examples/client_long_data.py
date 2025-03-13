from winConnect import WinConnectClient

connector = WinConnectClient('test')

i = b'i' * 1024 * 1024
with connector as conn:
    print(f"Sending {len(i)/1024}kb...")
    conn.send_data(i)
    data = conn.read_pipe()
    print(f"({type(data)}) {data[:9]=}; ok={data == i}")
