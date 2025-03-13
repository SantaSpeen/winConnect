import logging

from .crypto_class_base import WinConnectCryptoBase
from winConnect.exceptions import (
    WinConnectCryptoBadModeException,
    WinConnectCryptoException,
)

def test_crypto_class(crypto_class: "WinConnectCryptoBase"):
    if not isinstance(crypto_class, WinConnectCryptoBase):
        raise WinConnectCryptoBadModeException("crypto_class must be a subclass of WinConnectCryptoBase")
    if not crypto_class.test():
        raise WinConnectCryptoException("crypto_class failed test (test_bytes != decrypt_bytes)")

class WinConnectCrypto:

    def __init__(self):
        self.__crypto_class = None
        self.__log_prefix = None
        self._log = logging.getLogger("WinConnectCrypto")

    def set_crypto_class(self, crypto_class: "WinConnectCryptoBase"):
        self._log.debug(f"{self.__log_prefix}Updating crypto class. {self.get_info()} -> {crypto_class.__class__.__name__}")
        test_crypto_class(crypto_class)
        self.__crypto_class = crypto_class
        self.__log_prefix = f"[{self.get_info()}] "
        self._log.debug(f"{self.__log_prefix}Crypto class updated.")

    def set_logger(self, logger):
        logger.debug(f"{self.__log_prefix}Setting logger")
        self._log = logger

    def test_and_load(self) -> bool:
        self._log.debug(f"{self.__log_prefix}Testing and loading crypto class")
        if not self.__crypto_class.test():
            return False
        self.__crypto_class.load()
        self._log.debug(f"{self.__log_prefix}Crypto class loaded")
        return True

    def get_info(self):
        return self.__crypto_class.__class__.__name__

    def encrypt(self, data: bytes) -> bytes:
        return self.__crypto_class.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self.__crypto_class.decrypt(data)
