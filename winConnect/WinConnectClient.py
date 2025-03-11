import win32file

from winConnect.WinConnectBase import WinConnectBase


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
        self._client_connected = True

    def _init(self):
        self._send_message("command", b"get_session_settings:")
        self._init_session()

    def connect(self):
        self._open_pipe()

    def init_session(self):
        self._init()

    def read_pipe(self):
        if not self._client_connected:
            self.connect()
        if not self._inited:
            self.init_session()
        return self._parse_action(*self._read_message())

