import sys

from loguru import logger

from winConnect import WinConnectDaemon
from winConnect import crypto

logger.remove()
logger.add(sys.stdout, level="DEBUG")

crypt_mode = crypto.WinConnectCryptoSimple()

connector = WinConnectDaemon('test')
connector.set_logger(logger)
connector.set_crypto(crypt_mode)

for data in connector.listen():
    print(f"({type(data)}) {data=}")
    if data is None and connector.closed:
        break
    connector.send_data(data)
