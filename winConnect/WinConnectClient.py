import pywintypes
import win32file

from winConnect.WinConnectBase import WinConnectBase
from winConnect.exceptions import WinConnectConnectionNoPipeException


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
        except pywintypes.error as e:
            if e.winerror == 2:
                exc = WinConnectConnectionNoPipeException(f"Error while opening pipe: Pipe not found")
                exc.real_exc = e
                raise exc
            raise e

    def _init(self):
        self._send_message("command", b"get_session_settings:")
        self._init_session()

    def connect(self):
        """Connect to server"""
        self._open_pipe()
        return self.init_session()

    def init_session(self):
        """Init session with server: get session settings"""
        self._init()
        return self

    def _close_session(self):
        """Send close command to server"""
        if not self.closed:
            self._send_message("command", b"close:")

    def __enter__(self):
        if not self._connected:
            self.connect()
        if not self._inited:
            self.init_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self._close_session()
        self.close()

    def read_pipe(self):
        if not self._connected:
            self.connect()
        if not self._inited:
            self.init_session()
        return self._read()
