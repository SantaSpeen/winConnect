class WinConnectCryptoBase:

    @property
    def salt(self) -> bytes:
        return b""
    @salt.setter
    def salt(self, value): ...

    def encrypt(self, data: bytes) -> bytes: ...
    def decrypt(self, data: bytes) -> bytes: ...

    def test(self, test_bytes: bytes = b"test_string") -> bool:
        encrypted = self.encrypt(test_bytes)
        decrypted = self.decrypt(encrypted)
        if decrypted != test_bytes:
            return False
        return True

    def load(self) -> None: ...
    def unload(self) -> None: ...
