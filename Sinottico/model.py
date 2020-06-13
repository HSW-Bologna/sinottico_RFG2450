from adt import adt, Case
from typing import List


class SerialConfig:
    def __init__(self,
                 port=None,
                 baud=38400,
                 data=8,
                 stop=1,
                 parity="None",
                 flowctrl="None",
                 end="CR+LF"):
        self.port = port
        self.baud = baud
        self.data = data
        self.stop = stop
        self.parity = parity
        self.flowctrl = flowctrl
        self.end = end

    def endBytes(self):
        return {
            "Niente": b'',
            "CR": b'\r',
            "LF": b'\n',
            "CR+LF": b'\r\n'
        }[self.end]

    def endStr(self):
        return self.endBytes().decode()


@adt
class WorkMessage:
    NEWPORT: Case[SerialConfig]
    SEND: Case[str]
    GETINFO: Case
    GETPOWER: Case
    MODE: Case[int]
    ATT: Case[float]
    GETATT: Case
    OUTPUT: Case[int]
    GETOUTPUT: Case
    LOG: Case
    SETFREQ: Case[int]
    HANDSHAKE: Case


@adt
class GuiMessage:
    SEND: Case[str]
    RECV: Case[str]
    SERIAL: Case[str]
    REVISION: Case[str]
    POWER: Case[int, int, int]
    ERROR: Case
    CONNECTED: Case
    ATTENUATION: Case[float]
    OUTPUT: Case[int]
    LOG: Case[str, int, str]
    DISCONNECTED: Case
    MODE: Case[int]
