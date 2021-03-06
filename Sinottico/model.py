from adt import adt, Case
from typing import List, Dict, Tuple


class DatiPotenza:
    def __init__(self):
        self.diretta: Dict[int, Dict[int, List[int]]] = {25: {}, 45: {}}
        self.riflessa: Dict[int, Dict[int, List[int]]] = {25: {}, 45: {}}
        self.ciscolatore = 0.2


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

    def set_to(self, new):
        self.__init__(new.port, new.baud, new.data, new.stop,
                      new.parity, new.flowctrl, new.end)


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
    FIND_DIRECT_COMBINATIONS: Case[str]
    FIND_REFLEX_COMBINATIONS: Case[Tuple[int, int, int, int], str]
    SAVE_PARAMETERS: Case[str, str, Tuple[int, int,
                                          int, int], Tuple[int, int, int, int]]
    SEND_PARAMETERS: Case[Tuple[int, int, int, int], Tuple[int, int, int, int]]


@adt
class ArduinoMessage:
    NEWPORT: Case[SerialConfig]
    TEMPERATURE: Case[int]


@adt
class GuiMessage:
    SEND: Case[str]
    RECV: Case[str]
    SERIAL: Case[str]
    REVISION: Case[str]
    POWER: Case[int, int, str]
    ERROR: Case[str]
    ERROR_ARDUINO: Case
    CONNECTED_RFG: Case
    CONNECTED_ARDUINO: Case
    ATTENUATION: Case[float]
    OUTPUT: Case[int]
    LOG: Case[str, int, str]
    DISCONNECTED_RFG: Case
    DISCONNECTED_ARDUINO: Case
    MODE: Case[int]
    RECONNECTED: Case
    DIRECT_COMBINATIONS_FOUND: Case[List]
    REFLEX_COMBINATIONS_FOUND: Case[List]
