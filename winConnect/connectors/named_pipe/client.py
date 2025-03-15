import pywintypes
import win32file

from winConnect.exceptions import WinConnectConnectionNoPipeException
from ._base import WinConnectNamedPipe
from .._base_client import WinConnectClient


class WinConnectPipeClient(WinConnectNamedPipe, WinConnectClient):
    # see: https://mhammond.github.io/pywin32/win32pipe__CreateNamedPipe_meth.html
    pipe_desiredAccess = win32file.GENERIC_READ | win32file.GENERIC_WRITE  # Access mode (read/write)
    pipe_shareMode = 0  # Share mode (None)
    pipe_sa = None  # Security attributes
    pipe_CreationDisposition = win32file.OPEN_EXISTING  # Open mode (open existing)
    pipe_flagsAndAttributes = 0  # Flags and attributes
    pipe_hTemplateFile  = None  # Template file

    def __init__(self, pipe_name: str):
        super().__init__(pipe_name)

    def _open_sock(self):
        try:
            self._pipe = win32file.CreateFile(
                self._pipe_name,
                self.pipe_desiredAccess,
                self.pipe_shareMode,
                self.pipe_sa,
                self.pipe_CreationDisposition,
                self.pipe_flagsAndAttributes,
                self.pipe_hTemplateFile
            )
            self._opened = True
            self._connected = True
            self._log.debug(f"[{self._pipe_name}] Pipe opened")
        except pywintypes.error as e:
            if e.winerror == 2:
                exc = WinConnectConnectionNoPipeException(f"Error while opening pipe: Pipe not found")
                exc.real_exc = e
                raise exc
            raise e
