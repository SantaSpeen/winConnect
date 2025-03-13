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
        self.__crypto_class: WinConnectCryptoBase = None
        self.__log_prefix = None
        self._log = logging.getLogger("WinConnectCrypto")

    @property
    def crypt_name(self) -> str:
        return self.__crypto_class.__class__.__name__

    @property
    def crypt_salt(self) -> bytes:
        return self.__crypto_class.salt

    def set_salt(self, salt: bytes):
        self.__crypto_class.salt = salt

    def set_crypto_class(self, crypto_class: "WinConnectCryptoBase"):
        self._log.debug(f"{self.__log_prefix}Updating crypto class. {self.crypt_name} -> {crypto_class.__class__.__name__}")
        test_crypto_class(crypto_class)
        self.__crypto_class = crypto_class
        self.__log_prefix = f"[{self.crypt_name}] "
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

    def encrypt(self, data: bytes) -> bytes:
        return self.__crypto_class.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self.__crypto_class.decrypt(data)
