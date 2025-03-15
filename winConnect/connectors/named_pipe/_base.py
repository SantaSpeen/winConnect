import logging

import pywintypes
import win32file

from winConnect import exceptions
from .._base_base import WinConnectBase


class WinConnectNamedPipe(WinConnectBase):
    def __init__(self, pipe_name: str):
        super().__init__()
        self._log = logging.getLogger(f"WinConnectNamedPipe:{pipe_name}")
        self._pipe_name = r'\\.\pipe\{}'.format(pipe_name)
        self._sock = None

    @property
    def pipe_path(self):
        return self._pipe_name

    def __raw_read(self, size):
        with self._pipe_lock:
            try:
                _, data = win32file.ReadFile(self._sock, size)
                return data
            except pywintypes.error as e:
                if e.winerror == 109:
                    exc = exceptions.WinConnectConnectionClosedException("Connection closed")
                    exc.real_exc = e
                    raise exc
                raise e

    def __raw_write(self, packet):
        with self._pipe_lock:
            if self.closed:
                raise exceptions.WinConnectSessionClosedException("Session is closed")
            win32file.WriteFile(self._sock, packet)

    def _close_pipe(self):
        win32file.CloseHandle(self._sock)
