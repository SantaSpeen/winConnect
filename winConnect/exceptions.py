
class WinConnectBaseException(Exception): ...

# Struct
class WinConnectStructFormatException(WinConnectBaseException): ...

# Connection
class WinConnectConnectionException(WinConnectBaseException):
    """Base exception for connection"""
    real_exc = None
    ...

class WinConnectConnectionNoPipeException(WinConnectConnectionException):
    """No pipe found"""
    ...

class WinConnectConnectionClosedException(WinConnectConnectionException):
    """Connection closed"""
    ...

class WinConnectConnectionAlreadyOpenException(WinConnectConnectionException):
    """Connection already open"""
    ...


# Bad data (?)
class WinConnectBadDataTypeException(WinConnectBaseException): ...

# Session
class WinConnectSessionAlreadyActiveException(WinConnectBaseException): ...

class WinConnectSessionClosedException(WinConnectBaseException): ...

