import os
import random
from pathlib import Path

from .crypto_class_base import WinConnectCryptoBase
from winConnect.exceptions import WinConnectCryptoSimpleBadHeaderException

_pip_crypto = True
try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Cipher import PKCS1_OAEP
except ImportError:
    _pip_crypto = False


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
        header = f"wccs{shift_key}{key+shift_key}:".encode()
        for char in data:
            encrypted_text.append(char ^ key)
        return header + bytes(encrypted_text)

    def decrypt(self, data: bytes) -> bytes:
        try:
            header, content = data.split(b":", 1)
            if header[:4] != b"wccs":
                raise WinConnectCryptoSimpleBadHeaderException(f"Bad header in message: {header[:4].decode()}")
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
        if not _pip_crypto:
            raise ImportError("Crypto library not installed. Install with 'pip install winConnect[crypto]'")
        self.password = password
        self.__salt = os.urandom(16)
        self.__key = PBKDF2(password, self.__salt, dkLen=32, count=100000)

    @property
    def salt(self):
        return self.__salt

    @salt.setter
    def salt(self, value):
        self.__salt = value
        self.__key = PBKDF2(self.password, self.__salt, dkLen=32, count=100000)

    def encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(16)  # Генерируем IV
        header = b"wccp" + iv
        cipher = AES.new(self.__key, AES.MODE_CBC, iv)
        pad_len = 16 - len(data) % 16
        padded_data = data + bytes([pad_len] * pad_len)
        return header + cipher.encrypt(padded_data)  # Шифруем

    def decrypt(self, data: bytes) -> bytes:
        try:
            header, iv, content = data[:4], data[4:20], data[20:]
            if header[:4] != b"wccp":
                raise WinConnectCryptoSimpleBadHeaderException(f"Bad header in message: {header.decode()}")
        except ValueError:
            raise WinConnectCryptoSimpleBadHeaderException("No header in message.")

        cipher = AES.new(self.__key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(content)
        pad_len = decrypted[-1]  # Убираем PKCS7 padding
        return decrypted[:-pad_len]

# class WinConnectCryptoCert(WinConnectCryptoBase):
#     def __init__(self, cert_file: str):
#         if not _pip_crypto:
#             raise ImportError("Crypto library not installed. Install with 'pip install winConnect[crypto]'")
#         self.cert_file = Path(cert_file)
#
#     def _open_cert(self):
#         pass
#
#     def load(self) -> None:
#         self._open_cert()
#
#     def encrypt(self, data: bytes) -> bytes:
#         pass
#
#     def decrypt(self, data: bytes) -> bytes:
#         pass
#
