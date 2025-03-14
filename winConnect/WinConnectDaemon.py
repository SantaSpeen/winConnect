import win32pipe

from .WinConnectBase import WinConnectBase


class WinConnectDaemon(WinConnectBase):
    # see: https://mhammond.github.io/pywin32/win32pipe__CreateNamedPipe_meth.html
    pipe_openMode = win32pipe.PIPE_ACCESS_DUPLEX  # Open mode (read/write)
    pipe_pipeMode = win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT  # Pipe mode (message type, message read mode, blocking mode)
    pipe_nMaxInstances = 1  # Max number of instances
    pipe_nDefaultTimeOut = 0  # ~ ms
    pipe_sa = None  # Security attributes

    def __init__(self, pipe_name: str):
        super().__init__(pipe_name)
        self.run = True

    def _open_pipe(self):
        pipe_nOutBufferSize, pipe_nInBufferSize = self._body_max_size+20, self._body_max_size+20
        self._log.debug(f"[{self._pipe_name}] Creating pipe. "
                        f"Settings: {self.pipe_openMode=}, {self.pipe_pipeMode=}, {self.pipe_nMaxInstances=}, "
                        f"{pipe_nOutBufferSize=}, {pipe_nInBufferSize=}, {self.pipe_nDefaultTimeOut=}, {self.pipe_sa=}")
        self._pipe = win32pipe.CreateNamedPipe(
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

    def _close_session(self):
        self.run = False

    def wait_client(self):
        if not self._opened:
            self._open_pipe()
        win32pipe.ConnectNamedPipe(self._pipe, None)
        self._connected = True
        self._log.debug(f"[{self._pipe_name}] Client connected")

    def read_pipe(self):
        if not self._connected:
            self.wait_client()
        if not self._inited:
            self._init_session()
        # if not self._read():
        #     raise
        return self._read()

    def listen(self):
        while self.run:
            yield self.read_pipe()
        self.stop()

    def stop(self):
        self.run = False
        self.close()
