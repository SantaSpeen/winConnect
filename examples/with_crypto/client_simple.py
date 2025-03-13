import sys

from loguru import logger

from winConnect import WinConnectClient, crypto

logger.remove()
logger.add(sys.stdout, level="DEBUG")

crypt_mode = crypto.WinConnectCryptoSimple()

connector = WinConnectClient('test')
connector.set_logger(logger)
connector.set_crypto(crypt_mode)

def console():
    with connector as conn:
        while True:
            i = input(":> ")
            if i == "exit":
                break
            conn.send_data(i)
            data = conn.read_pipe()
            print(f"({type(data)}) {data=}")

if __name__ == '__main__':
    console()
