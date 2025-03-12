import sys

from loguru import logger
from winConnect import WinConnectDaemon

connector = WinConnectDaemon('test')

logger.remove()
logger.add(sys.stdout, level="DEBUG")

connector.set_logger(logger)

for data in connector.listen():
    print(f"({type(data)}) {data=}")
    if data is None and connector.closed:
        break
    connector.send_data(data)
