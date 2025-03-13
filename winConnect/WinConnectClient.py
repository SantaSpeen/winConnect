import pywintypes
import win32file

from .WinConnectBase import WinConnectBase
from .exceptions import WinConnectConnectionNoPipeException


class WinConnectClient(WinConnectBase):
    # see: https://mhammond.github.io/pywin32/win32pipe__CreateNamedPipe_meth.html
    pipe_desiredAccess = win32file.GENERIC_READ | win32file.GENERIC_WRITE  # Access mode (read/write)
    pipe_shareMode = 0  # Share mode (None)
    pipe_sa = None  # Security attributes
    pipe_CreationDisposition = win32file.OPEN_EXISTING  # Open mode (open existing)
    pipe_flagsAndAttributes = 0  # Flags and attributes
    pipe_hTemplateFile  = None  # Template file

    def __init__(self, pipe_name: str):
        super().__init__(pipe_name)

    def _open_pipe(self):
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

    def _init(self, program_name="NoName"):
        self._send_message("cmd", b"get_session_settings:" + program_name.encode(self.encoding))
        self._init_session()

    def _close_session(self):
        """Send close command to server"""
        if not self.closed:
            self._send_message("cmd", b"close:")

    def __check_pipe(self):
        if not self._opened:
            self._open_pipe()
        if not self._inited:
            self._init()

    def __enter__(self):
        self.__check_pipe()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self, program_name: str="NoName"):
        """Connect to server and initialize session"""
        self._open_pipe()
        self._init(program_name)
        return self

    def read_pipe(self):
        self.__check_pipe()
        return self._read()
