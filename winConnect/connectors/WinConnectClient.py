from winConnect.connectors.WinConnectBase import WinConnectBase


class WinConnectClient(WinConnectBase):

    def __init__(self, pipe_name: str):
        super().__init__(pipe_name)

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
