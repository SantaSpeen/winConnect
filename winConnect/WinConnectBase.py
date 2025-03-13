import hashlib
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

    read_max_buffer = SimpleConvertor.to_gb(3)-32  # Max size via chunked messages

    ormsgpack_options = ormsgpack.OPT_NON_STR_KEYS | ormsgpack.OPT_NAIVE_UTC | ormsgpack.OPT_PASSTHROUGH_TUPLE # ormsgpack options

    def __init__(self, pipe_name: str):
        self._log = logging.getLogger(f"WinConnect:{pipe_name}")
        # versions:
        # 1 - 0.9.1
        # 2 - 0.9.2 (with crypto)
        # 3 - 0.9.3+ (with crypto+salt)
        self._version = 3
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

        self._pipe_lock = threading.Lock()
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()

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
        # Max size of body: struct_range - header_size - crypt_fix - action_and_data
        # - header_size; X byte for header_size
        # - crypt_fix; 32 byte for crypto fix (internal data)
        # - action_and_data; 8 byte for action and data (internal data)  act:typ: = 8 byte
        self._body_max_size = SimpleConvertor.struct_range(self._header_format)[1] - self._header_size - 32 - 8
        if self._body_max_size-64 < 0:
            raise exceptions.WinConnectBaseException("Header size is too small")

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

    @staticmethod
    def __parse_message(message: bytes):
        return message.split(b":", 1)

    def _open_pipe(self): ...

    def __handle_send_data(self, action, data) -> bytes:
        t = type(data)
        if t == bytes or t == bytearray:
            data_type = b"raw"
            ready_data = bytes(data)
        else:
            data_type = b"msg"
            ready_data = ormsgpack.packb(data, option=self.ormsgpack_options)
        return data_type + b":" + action + b":" + zlib.compress(ready_data)

    def __handle_receive_data_type(self, data):
        data_type, action_data = self.__parse_message(data)
        action, data = self.__parse_message(action_data)
        data = zlib.decompress(data)
        match data_type:
            case b"raw":
                ready_data = data
            case b"msg":
                ready_data = ormsgpack.unpackb(data)
            case _:
                self._send_error(WinConnectErrors.UNKNOWN_DATA_TYPE, f"Unknown data type '{data_type}'")
                raise exceptions.WinConnectBadDataTypeException('Is client using correct lib? Unknown data type')
        return action, ready_data

    def __raw_read(self, size):
        with self._pipe_lock:
            try:
                _, data = win32file.ReadFile(self._pipe, size)
                return data
            except pywintypes.error as e:
                if e.winerror == 109:
                    exc = exceptions.WinConnectConnectionClosedException("Connection closed")
                    exc.real_exc = e
                    raise exc
                raise e

    def __read_and_decrypt(self, size):
        data = self.__raw_read(size)
        if self._inited:
            data = self.__crypto.decrypt(data)
        return data

    def _read_message(self) -> (str, Any):
        with self._read_lock:
            _hfmt, _hsize = self.__header_settings
            # Read header
            header = self.__raw_read(_hsize)
            if not header:
                self._send_error(WinConnectErrors.BAD_HEADER, f"No header received")
                self.close()
            if len(header) != _hsize and self._inited:
                self._send_error(WinConnectErrors.BAD_HEADER, f"Bad header size. Expected: {_hsize}, got: {len(header)}")
                self.close()
            message_size = struct.unpack(_hfmt, header)[0]
            if message_size > self._body_max_size:
                self._send_error(WinConnectErrors.BODY_TOO_BIG, f"Body is too big. Max size: {self._body_max_size}kb")
                self.close()
            if not self._connected:
                return None, None
            # Read body
            data = self.__read_and_decrypt(message_size)
            action, data = self.__handle_receive_data_type(data)
            self._log.debug(f"[{self._pipe_name}] Received message: {action=} {data=}")
            return action, data

    def __raw_write(self, packet):
        with self._pipe_lock:
            if self.closed:
                raise exceptions.WinConnectSessionClosedException("Session is closed")
            win32file.WriteFile(self._pipe, packet)

    def _send_message(self, action: str, data: Any):
        with self._write_lock:
            action = action.encode(self.encoding)
            packed_data = self.__handle_send_data(action, data)
            if self._inited:
                packed_data = self.__crypto.encrypt(packed_data)

            message_size = len(packed_data)
            if message_size > self._body_max_size:
                raise exceptions.WinConnectBaseException('Message is too big')

            self._log.debug(f"[{self._pipe_name}] Sending message: {action=} {data=}; {message_size} {packed_data=}")
            # Send header
            self.__raw_write(struct.pack(self.__header_settings[0], message_size))
            # Send body
            self.__raw_write(packed_data)

    def _send_error(self, error: WinConnectErrors, error_message: str = None):
        e = {"error": True, "code": error.value, "message": error.name, "description": error_message}
        self._send_message("err", e)

    def __read_chunked_message(self, data_info: bytes):
        self._log.debug(f"[{self._pipe_name}] Receive long message. Reading in chunks...")
        chunk_size = self._body_max_size - 32
        sha256, data_len = data_info[:32], int(data_info[32:])
        if data_len > self.read_max_buffer:
            self._send_error(WinConnectErrors.BODY_TOO_BIG, f"Body is too big. Max size: {self.read_max_buffer}kb")
            self.close()
        _buffer = b""

        with self._read_lock:
            for i in range(0, data_len, chunk_size):
                _buffer += self.__read_and_decrypt(chunk_size)

        return _buffer

    def __send_chunked_message(self, data: bytes):
        self._log.debug(f"[{self._pipe_name}] Long message. Sending in chunks...")
        chunk_size = self._body_max_size - 32
        cdata = zlib.compress(data)

        cdata_len = len(cdata)
        if cdata_len > self.read_max_buffer:
            raise exceptions.WinConnectBaseException(f'Message is too big. Change WinConnectBase.read_max_buffer. Now is: {self.read_max_buffer/1024}kb')
        cdata_sha256 = hashlib.sha256(cdata).digest()
        self._send_message("dtc", cdata_sha256 + str(cdata_len).encode(self.encoding))

        with self._write_lock:
            for i in range(0, cdata_len, chunk_size):
                _encrypted = self.__crypto.encrypt(cdata[i:i + chunk_size])
                self.__raw_write(_encrypted)

    def _parse_action(self, action, data: Any) -> (bool, Any):
        # return: (internal_action, data)
        if not self._connected:
            return
        match action:
            case b"cmd":  # Command
                return True, self._parse_command(data)
            case b"dtn":  # Data normal
                return False, data
            case b"dtc":  # Data chunked
                return False, self.__read_chunked_message(data)
            case b"err":
                return False, WinConnectError(data['code'], data['message'])
            case _:
                return self._send_error(WinConnectErrors.UNKNOWN_ACTION, f"Unknown action '{action}'")

    def _parse_command(self, data: bytes):
        _blank_settings = {
            'version': None,
            'encoding': None,
            'header_size': None,
            'header_format': None,
            'max_buffer': None,
            'crypto': None
        }
        command, data = self.__parse_message(data)
        match command:
            case b'get_session_settings':
                self._log.debug(f"[{self._pipe_name}] Received get_session_settings from {data}")
                _blank_settings['version'] = self._version
                _blank_settings['encoding'] = self._session_encoding
                _blank_settings['header_size'] = self._header_size
                _blank_settings['header_format'] = self._header_format
                _blank_settings['max_buffer'] = self.read_max_buffer
                _blank_settings['crypto'] = self.__crypto.crypt_name
                session_settings = f"set_session_settings:{len(self.__crypto.crypt_salt)}:{json.dumps(_blank_settings)}".encode(self.encoding) + self.__crypto.crypt_salt
                self._send_message("cmd", session_settings)
                return True
            case b'set_session_settings':
                self._log.debug(f"[{self._pipe_name}] Received session settings.")
                len_salt, data = self.__parse_message(data)
                len_salt = int(len_salt)
                data, salt = data[:-len_salt], data[-len_salt:]

                if salt != self.__crypto.crypt_salt:
                    self._log.debug(f"[{self._pipe_name}] Updating salt")
                    self.__crypto.set_salt(salt)

                try:
                    settings = json.loads(data.decode(self.init_encoding))
                except json.JSONDecodeError as e:
                    self._send_error(WinConnectErrors.BAD_DATA, f"JSONDecodeError: {e}")
                    return self.close()

                if _blank_settings.keys() != settings.keys():
                    self._log.error(f"{WinConnectErrors.BAD_SETTINGS}")
                    self._send_error(WinConnectErrors.BAD_SETTINGS, f"Setting have wrong structure")
                    return self.close()

                if settings['version'] != self._version:
                    self._log.error(f"{WinConnectErrors.BAD_VERSION}")
                    self._send_error(WinConnectErrors.BAD_VERSION, f"Version mismatch")
                    return self.close()
                if settings['crypto'] != self.__crypto.crypt_name:
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
        if action != b"cmd":
            return self._send_error(WinConnectErrors.BAD_DATA, "Unknown data type")
        if not self._parse_command(data):
            return self._send_error(WinConnectErrors.INIT_FIRST, "Server need to init session first")
        self._send_message("cmd", b"session_ready:")
        self._parse_action(*self._read_message())

    def send_data(self, data):
        if len(data) > self._body_max_size:
            return self.__send_chunked_message(data)
        self._send_message("dtn", data)

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
