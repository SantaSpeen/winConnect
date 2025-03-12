import uuid

from winConnect import WinConnectClient

connector = WinConnectClient('test')

test_data = (
    [1, 2, 3, 4, 5],  # List
    # {"test"},  # Set - Not supported
    {"test": "test"},  # Dict
    "test",  # Str
    123,  # Int
    123.456,  # Float
    None,  # None
    True,  # Bool
    uuid.uuid4()  # UUID; Transformed to str
)

def send_data():
    with connector as conn:
        for i in test_data:
            conn.send_data(i)
            data = conn.read_pipe()
            print(f"({type(data)}) {data=}")

if __name__ == '__main__':
    send_data()
