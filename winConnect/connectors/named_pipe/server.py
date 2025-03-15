import win32pipe

from ._base import WinConnectNamedPipe
from .._base_server import WinConnectServer


class WinConnectPipeServer(WinConnectNamedPipe, WinConnectServer):
    # see: https://mhammond.github.io/pywin32/win32pipe__CreateNamedPipe_meth.html
    pipe_openMode = win32pipe.PIPE_ACCESS_DUPLEX  # Open mode (read/write)
    pipe_pipeMode = win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT  # Pipe mode (message type, message read mode, blocking mode)
    pipe_nMaxInstances = 1  # Max number of instances
    pipe_nDefaultTimeOut = 0  # ~ ms
    pipe_sa = None  # Security attributes

    def __init__(self, pipe_name: str):
        super().__init__(pipe_name)
        self.run = True

    def _open_sock(self):
        pipe_nOutBufferSize, pipe_nInBufferSize = self._body_max_size+20, self._body_max_size+20
        self._log.debug(f"[{self._pipe_name}] Creating pipe. "
                        f"Settings: {self.pipe_openMode=}, {self.pipe_pipeMode=}, {self.pipe_nMaxInstances=}, "
                        f"{pipe_nOutBufferSize=}, {pipe_nInBufferSize=}, {self.pipe_nDefaultTimeOut=}, {self.pipe_sa=}")
        self._sock = win32pipe.CreateNamedPipe(
            self._pipe_name,
            self.pipe_openMode,
            self.pipe_pipeMode,
            self.pipe_nMaxInstances,
            pipe_nOutBufferSize,
            pipe_nInBufferSize,
            self.pipe_nDefaultTimeOut,
            self.pipe_sa
        )
        self._opened = True
        self._log.debug(f"[{self._pipe_name}] Pipe opened")

    def _wait_connect(self):
        win32pipe.ConnectNamedPipe(self._sock, None)
