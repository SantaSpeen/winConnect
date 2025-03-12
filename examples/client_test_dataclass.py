from dataclasses import dataclass

from winConnect import WinConnectClient

connector = WinConnectClient('test')

# Dataclass covert to json and send to server
@dataclass
class TestUser:
    name: str
    age: int

def send_data():
    i = TestUser("test", 123)
    with connector as conn:
        conn.send_data(i)
        data = conn.read_pipe()
        print(f"({type(data)}) {data=}")

if __name__ == '__main__':
    send_data()
