import win32pipe

from winConnect.WinConnectBase import WinConnectBase
from winConnect.utils import SimpleConvertor


class WinConnectDaemon(WinConnectBase):
    # see: https://mhammond.github.io/pywin32/win32pipe__CreateNamedPipe_meth.html
    pipe_openMode = win32pipe.PIPE_ACCESS_DUPLEX  # Open mode (read/write)
    pipe_pipeMode = win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT  # Pipe mode (message type, message read mode, blocking mode)
    pipe_nMaxInstances = 2  # Max number of instances
    pipe_nOutBufferSize = SimpleConvertor.to_kb(64)  # Max size of output buffer
    pipe_nInBufferSize = SimpleConvertor.to_kb(64)  # Max size of input buffer
    pipe_nDefaultTimeOut = 0  # ~ ms
    pipe_sa = None  # Security attributes

    def __init__(self, pipe_name: str):
        super().__init__(pipe_name)

    def _open_pipe(self):
        self._pipe = win32pipe.CreateNamedPipe(
            self._pipe_name,
            self.pipe_openMode,
            self.pipe_pipeMode,
            self.pipe_nMaxInstances,
            self.pipe_nOutBufferSize,
            self.pipe_nInBufferSize,
            self.pipe_nDefaultTimeOut,
            self.pipe_sa
        )
        self._opened = True

    def wait_client(self):
        if not self._opened:
            self._open_pipe()
        win32pipe.ConnectNamedPipe(self._pipe, None)
        self._connected = True

    def read_pipe(self):
        if not self._connected:
            self.wait_client()
        if not self._inited:
            self._init_session()
        # if not self._read():
        #     raise
        return self._read()
