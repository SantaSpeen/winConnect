import json
import logging
import struct
import threading
import zlib
from typing import Any

import ormsgpack
import pywintypes
import win32file

from .crypto.WinConnectCrypto import WinConnectCrypto
from .crypto.crypto_classes import WinConnectCryptoNone
from .errors import WinConnectErrors, WinConnectError
from . import exceptions
from .utils import SimpleConvertor

# header: len(data) in struct.pack via header_format
# data: action:data
# headerDATA

class WinConnectBase:
    init_encoding = 'utf-8'
    init_header_format = ">H"  # Format for reading header (big-endian, unsigned long; 4 bytes)

    default_encoding = 'utf-8'

    read_max_buffer = SimpleConvertor.to_gb(3)-1  # Max size via chunked messages

    ormsgpack_options = ormsgpack.OPT_NON_STR_KEYS | ormsgpack.OPT_NAIVE_UTC | ormsgpack.OPT_PASSTHROUGH_TUPLE # ormsgpack options

    def __init__(self, pipe_name: str):
        self._log = logging.getLogger(f"WinConnect:{pipe_name}")
        # _version:
        # 1 - 0.9.1
        # 2 - 0.9.2+ (with crypto)
        self._version = 2
        self._pipe_name = r'\\.\pipe\{}'.format(pipe_name)
        self._pipe = None
        self._opened = False

        self._header_format = self.init_header_format
        self._header_size = struct.calcsize(self._header_format)  # bytes
        self._calc_body_max_size()

        self._connected = False
        self._inited = False
        self._session_encoding = self.init_encoding

        self.__crypto = WinConnectCrypto()
        self.__crypto.set_crypto_class(WinConnectCryptoNone())

        # self._chunks = []

        self._lock = threading.Lock()

    def set_crypto(self, crypto):
        if self._connected:
            raise exceptions.WinConnectConnectionAlreadyOpenException("Can't change crypto while session is active")
        self.__crypto.set_crypto_class(crypto)
        if not self.__crypto.test_and_load():
            raise exceptions.WinConnectCryptoException("Crypto failed test")

    def set_logger(self, logger):
        logger.debug(f"[{self._pipe_name}] Update logger")
        self._log = logger
        self.__crypto.set_logger(logger)

    def _calc_body_max_size(self):
        # Max size of body: 2 ** (8 * header_size) - 1 - header_size - 1
        # - header_size; X byte for header_size
        self._body_max_size = SimpleConvertor.struct_range(self._header_format)[1] - self._header_size

    def set_header_settings(self, fmt):
        if self._connected:
            raise exceptions.WinConnectSessionAlreadyActiveException("Session is active. Can't change header settings")
        try:
            self._header_format = fmt
            self._header_size = struct.calcsize(fmt)
            self._calc_body_max_size()
        except struct.error as e:
            raise exceptions.WinConnectStructFormatException(f"Error in struct format. ({e})")

    @property
    def pipe_name(self):
        return self._pipe_name

    @property
    def encoding(self):
        if not self._inited:
            return self.init_encoding
        return self._session_encoding

    @property
    def __header_settings(self):
        if not self._inited:
            return self.init_header_format, struct.calcsize(self.init_header_format)
        return self._header_format, self._header_size

    @property
    def closed(self):
        return not self._connected

    def _open_pipe(self): ...

    def __pack_data(self, action, data) -> (bytes, bytes):
        data_type = "msg"
        data = ormsgpack.packb(data, option=self.ormsgpack_options)
        compressed_data = zlib.compress(data)
        return data_type.encode(self.encoding) +  b":" + action + b":" + compressed_data

    def __unpack_data(self, data: bytes) -> (str, Any):
        data_type, action_data = self.__parse_message(data)
        if data_type != b"msg":
            self._send_error(WinConnectErrors.UNKNOWN_DATA_TYPE, f"Unknown data type '{data_type}'")
            raise exceptions.WinConnectBadDataTypeException('Is client using correct lib? Unknown data type')
        action, data = self.__parse_message(action_data)
        decompressed_data = zlib.decompress(data)
        deserialized_data = ormsgpack.unpackb(decompressed_data)
        return action, deserialized_data

    @staticmethod
    def __parse_message(message: bytes):
        return message.split(b":", 1)

    def _read_message(self) -> (str, Any):
        with self._lock:
            _hfmt, _hsize = self.__header_settings
            try:
                _, header = win32file.ReadFile(self._pipe, self._header_size)
            except pywintypes.error as e:
                if e.winerror == 109:
                    exc = exceptions.WinConnectConnectionClosedException("Connection closed")
                    exc.real_exc = e
                    raise exc
                raise e
            if not header:
                return b""
            if len(header) != _hsize and self._inited:
                self._send_error(WinConnectErrors.BAD_HEADER, f"Bad header size. Expected: {_hsize}, got: {len(header)}")
                self.close()
            message_size = struct.unpack(_hfmt, header)[0]
            if message_size > self._body_max_size or message_size > self.read_max_buffer:
                self._send_error(WinConnectErrors.BODY_TOO_BIG, f"Body is too big. Max size: {self._body_max_size}kb")
                self.close()
            if not self._connected:
                return None, None
            _, data = win32file.ReadFile(self._pipe, message_size)
            if self._inited:
                data = self.__crypto.decrypt(data)
            action, data = self.__unpack_data(data)
            self._log.debug(f"[{self._pipe_name}] Received message: {action=} {data=}")
            return action, data

    def _send_message(self, action: str, data: Any):
        action = action.encode(self.encoding)
        with self._lock:
            if self.closed:
                raise exceptions.WinConnectSessionClosedException("Session is closed")
            packed_data = self.__pack_data(action, data)
            if self._inited:
                packed_data = self.__crypto.encrypt(packed_data)
            message_size = len(packed_data)
            if message_size > self._body_max_size:
                raise ValueError('Message is too big')
            # Если размер сообщения больше размера read_header_size, то ошибка
            if message_size > 2 ** (8 * self._header_size):
                raise ValueError('Message is too big')
            _hfmt, _ = self.__header_settings
            header = struct.pack(_hfmt, message_size)
            packet = header + packed_data
            self._log.debug(f"[{self._pipe_name}] Sending message: {action=} {data=}; {packet=}")
            win32file.WriteFile(self._pipe, packet)

    def _send_error(self, error: WinConnectErrors, error_message: str = None):
        e = {"error": True, "code": error.value, "message": error.name, "description": error_message}
        self._send_message("error", e)

    def _parse_action(self, action, data: Any) -> (bool, Any):
        # return: (internal_command, data)
        if not self._connected:
            return
        match action:
            case b"command":
                return True, self._parse_command(data)
            case b"data":
                return False, data
            case b"error":
                return False, WinConnectError(data['code'], data['message'])
            case _:
                return self._send_error(WinConnectErrors.UNKNOWN_ACTION, f"Unknown action '{action}'")

    def _parse_command(self, data: bytes):
        command, data = self.__parse_message(data)
        match command:
            case b'get_session_settings':
                self._log.debug(f"[{self._pipe_name}] Received get_session_settings from {data}")
                settings = {
                    'version': self._version,
                    'encoding': self.default_encoding,
                    'header_size': self._header_size,
                    'header_format': self._header_format,
                    'max_buffer': self.read_max_buffer,
                    "crypto": self.__crypto.get_info()
                }
                session_settings = f"set_session_settings:{json.dumps(settings)}".encode(self.init_encoding)
                self._send_message("command", session_settings)
                return True
            case b'set_session_settings':
                try:
                    settings = json.loads(data.decode(self.init_encoding))
                except json.JSONDecodeError as e:
                    self._send_error(WinConnectErrors.BAD_DATA, f"JSONDecodeError: {e}")
                    return self.close()
                if settings.get('version') != self._version:
                    self._log.error(f"{WinConnectErrors.BAD_VERSION}")
                    self._send_error(WinConnectErrors.BAD_VERSION, f"Version mismatch")
                    return self.close()
                if settings.get('crypto') != self.__crypto.get_info():
                    self._log.error(f"{WinConnectErrors.BAD_CRYPTO}")
                    self._send_error(WinConnectErrors.BAD_CRYPTO, f"Crypto mismatch")
                    return self.close()
                self._session_encoding = settings.get('encoding', self.default_encoding)
                self._header_size = settings.get('header_size', self._header_size)
                self._header_format = settings.get('header_format', self._header_format)
                self.read_max_buffer = settings.get('max_buffer', self.read_max_buffer)
                return True
            case b"session_ready":
                self._inited = True
                return True
            case b"close":
                self.close()
                return True
            case _:
                return self._send_error(WinConnectErrors.UNKNOWN_COMMAND, f"Command {command!r} is unknown")

    def _init_session(self):
        action, data = self._read_message()
        if not self._connected:
            return
        if action != b"command":
            return self._send_error(WinConnectErrors.BAD_DATA, "Unknown data type")
        if not self._parse_command(data):
            return self._send_error(WinConnectErrors.INIT_FIRST, "Server need to init session first")
        self._send_message("command", b"session_ready:")
        self._parse_action(*self._read_message())

    def send_data(self, data):
        self._send_message("data", data)

    def _close_session(self): ...

    def close(self):
        self._close_session()
        if self._connected:
            win32file.CloseHandle(self._pipe)
            self._opened = False
            self._connected = False
            self._inited = False
            self._pipe = None
            self._log.debug(f"[{self._pipe_name}] Session closed")

    def _read(self) -> Any:
        if self.closed:
            return None
        internal, data = self._parse_action(*self._read_message())
        if internal:
            return self._read()
        return data

    def read_pipe(self):
        ...
