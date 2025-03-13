import random

from .crypto_class_base import WinConnectCryptoBase
from winConnect.exceptions import WinConnectCryptoSimpleBadHeaderException


class WinConnectCryptoNone(WinConnectCryptoBase):
    def __init__(self): ...
    def encrypt(self, data: bytes) -> bytes:
        return data
    def decrypt(self, data: bytes) -> bytes:
        return data

class WinConnectCryptoSimple(WinConnectCryptoBase):
    def __init__(self):
        pass

    def encrypt(self, data: bytes) -> bytes:
        shift_key = random.randint(100, 749)
        key = random.randint(5, 250)
        encrypted_text = bytearray()
        header = f"wccs{shift_key}{key+shift_key}:"
        for char in header:
            encrypted_text.append(ord(char))
        for char in data:
            encrypted_text.append(char ^ key)
        return bytes(encrypted_text)

    def decrypt(self, data: bytes) -> bytes:
        try:
            header, content = data.split(b":", 1)
            if header[:4] != b"wccs":
                raise WinConnectCryptoSimpleBadHeaderException("Bad header in message.")
        except ValueError:
            raise WinConnectCryptoSimpleBadHeaderException("No header in message.")
        shift_key = int(header[4:7])
        key = int(header[7:]) - shift_key
        decrypted_text = bytearray()
        for char in content:
            decrypted_text.append(char ^ key)
        return bytes(decrypted_text)


class WinConnectCryptoPassword(WinConnectCryptoBase):

    def __init__(self, password: str):
        pass

    def encrypt(self, data: bytes) -> bytes:
        pass

    def decrypt(self, data: bytes) -> bytes:
        pass

class WinConnectCryptoCert(WinConnectCryptoBase):
    def __init__(self, cert_file: str):
        pass

    def _open_cert(self):
        pass

    def load(self) -> None:
        self._open_cert()

    def encrypt(self, data: bytes) -> bytes:
        pass

    def decrypt(self, data: bytes) -> bytes:
        pass

