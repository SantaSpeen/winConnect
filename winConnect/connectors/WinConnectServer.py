import win32pipe

from winConnect.connectors.WinConnectBase import WinConnectBase


class WinConnectServer(WinConnectBase):

    def __init__(self, pipe_name: str):
        super().__init__(pipe_name)
        self.run = True

    def _open_pipe(self): ...

    def _wait_connect(self): ...

    def _close_session(self):
        self.run = False

    def wait_client(self):
        if not self._opened:
            self._open_pipe()
        self._wait_connect()
        self._connected = True
        self._log.debug(f"[{self._pipe_name}] Client connected")

    def read_pipe(self):
        if not self._connected:
            self.wait_client()
        if not self._inited:
            self._init_session()
        return self._read()

    def listen(self):
        while self.run:
            yield self.read_pipe()
        self.stop()

    def stop(self):
        self.run = False
        self.close()
