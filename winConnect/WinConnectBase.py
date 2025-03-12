import json
import pickle
import struct
import threading
import zlib
from enum import Enum
from typing import Any

import ormsgpack
import win32file

from winConnect.utils import SimpleConvertor


class WinConnectErrors(Enum):
    NO_ERROR = 0

    INIT_FIRST = 10

    UNKNOWN_DATA_TYPE = 30
    UNKNOWN_COMMAND = 31
    UNKNOWN_ACTION = 32

    BAD_DATA = 50
    BAD_VERSION = 51

# header: len(data) in struct.pack via header_format
# data: action:data
# headerDATA

class WinConnectBase:
    init_encoding = 'utf-8'
    init_header_format = ">L"  # Format for reading header (big-endian, unsigned long; 4 bytes)

    default_encoding = 'utf-8'

    read_max_buffer = SimpleConvertor.to_gb(4)  # Max size of buffer for message

    def __init__(self, pipe_name: str):
        self.run = True
        self._version = 1
        self._pipe_name = r'\\.\pipe\{}'.format(pipe_name)
        self._pipe = None
        self._opened = False

        self._header_format = self.init_header_format
        self._header_size = struct.calcsize(self._header_format)  # bytes
        self._calc_body_max_size()

        self._client_connected = False
        self._inited = False
        self._session_encoding = self.init_encoding

        self._parts_buffer = None  # Buffer for parts of message (If message is too big)

        self._lock = threading.Lock()

    def _calc_body_max_size(self):
        # Max size of body: 2 ** (8 * header_size) - 1 - header_size - 1
        # - header_size; X byte for header_size
        self._body_max_size = SimpleConvertor.struct_range(self._header_format)[1] - self._header_size

    def set_header_settings(self, fmt):
        if self._client_connected:
            raise WinConnectSessionAlreadyActiveError("Session is active. Can't change header settings")
        try:
            self._header_format = fmt
            self._header_size = struct.calcsize(fmt)
            self._calc_body_max_size()
        except struct.error as e:
            raise WinConnectStructFormatError(f"Error in struct format. ({e})")

    @property
    def pipe_name(self):
        return self._pipe_name

    @property
    def encoding(self):
        return self._session_encoding

    def _open_pipe(self): ...

    def __pack_data(self, action, data) -> (bytes, bytes):
        data_type = "msg"
        data = ormsgpack.packb(data, option=ormsgpack.OPT_NAIVE_UTC)
        compressed_data = zlib.compress(data)
        return data_type.encode(self._session_encoding) +  b":" + action + b":" + compressed_data

    def __unpack_data(self, data: bytes) -> (str, Any):
        data_type, action_data = self.__parse_message(data)
        if data_type != b"msg":
            raise ValueError('Is client using correct lib? Unknown data type')
        action, data = self.__parse_message(action_data)
        decompressed_data = zlib.decompress(data)
        deserialized_data = ormsgpack.unpackb(decompressed_data)
        return action, deserialized_data

    @staticmethod
    def __parse_message(message: bytes):
        return message.split(b":", 1)

    def _read_message(self) -> (str, Any):
        with self._lock:
            _, header = win32file.ReadFile(self._pipe, self.header_size)
            if not header:
                return b""
            if len(header) != self.header_size and self._inited:
                raise ValueError('Header is too small')
            message_size = struct.unpack(self.header_format, header)[0]
            _, data = win32file.ReadFile(self._pipe, message_size)
            return self.__unpack_data(data)

    def _send_message(self, action: str, data: Any):
        with self._lock:
            data = self.__pack_data(action.encode(self.encoding), data)
            message_size = len(data)
            if message_size > self.read_max_buffer:
                raise ValueError('Message is too big')
            # Если размер сообщения больше размера read_header_size, то ошибка
            if message_size > 2 ** (8 * self.header_size):
                raise ValueError('Message is too big')
            header = struct.pack(self.header_format, message_size)
            print("Sending message:", header, data)
            win32file.WriteFile(self._pipe, header)
            win32file.WriteFile(self._pipe, data)

    def _send_error(self, error: WinConnectErrors, error_message: str = None):
        e = {"error": True, "code": error.value, "message": error.name, "description": error_message}
        self._send_message("error", e)

    def _parse_action(self, action, data: bytes):
        match action:
            case b"command":
                return self._parse_command(data)
            case b"data":
                return data
            case b"error":
                print(data)
            case _:
                return self._send_error(WinConnectErrors.UNKNOWN_ACTION, f"Unknown action '{action}'")

    def _parse_command(self, data: bytes):
        command, data = self.__parse_message(data)
        match command:
            case b'get_session_settings':
                settings = {
                    'version': self._version,
                    'encoding': self.default_encoding,
                    'header_size': self.header_size,
                    'header_format': self.header_format,
                    'max_buffer': self.read_max_buffer
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
                    self._send_error(WinConnectErrors.BAD_VERSION, f"Version mismatch")
                    return self.close()
                self._session_encoding = settings.get('encoding', self.default_encoding)
                self.header_size = settings.get('header_size', self.header_size)
                self.header_format = settings.get('header_format', self.header_format)
                self.read_max_buffer = settings.get('max_buffer', self.read_max_buffer)
                self._send_message("command", b"ready:")
                return True
            case b"ready":
                return True
            case _:
                return self._send_error(WinConnectErrors.UNKNOWN_COMMAND, f"Command {command!r} is unknown")

    def _init_session(self):
        action, data = self._read_message()
        if action != b"command":
            return self._send_error(WinConnectErrors.BAD_DATA, "Unknown data type")
        if not self._parse_command(data):
            return self._send_error(WinConnectErrors.INIT_FIRST, "Server need to init session first")
        self._inited = True

    def send_data(self, data):
        self._send_message("data", data)

    def close(self):
        if self._opened:
            win32file.CloseHandle(self._pipe)
            self._opened = False
            self._client_connected = False
            self._inited = False
            self._pipe = None

    def read_pipe(self):
        ...

    def listen(self):
        while self.run:
            yield self.read_pipe()
        self.stop()

    def stop(self):
        self.run = False
        with self._lock:
            self.close()
