from abc import ABC, abstractmethod, abstractstaticmethod
from parse import parse  # type: ignore
import time

from ..model import *


def parseSerialNumber(string):
    if string.startswith('S/N,') and string.endswith('\r\n'):
        return string.replace('S/N,', '').replace('\r\n', '')
    else:
        return None

def parsePar(string):
    return parse("PAR,{},Wf,{},Wr,{},C\r\n", string)

class Command(ABC):
    def __init__(self, hidden=True):
        self.start()
        self.hidden = hidden
        self._error = False

    def error(self):
        return self._error

    def start(self):
        self.started = time.time()

    def timeout(self):
        return time.time() - self.started > 1

    @abstractmethod
    def commandString(self) -> str:
        pass

    @abstractmethod
    def parseResponse(self, response: str) -> bool:
        pass

    @abstractmethod
    def result(self) -> GuiMessage:
        pass


class CmdSet(Command):
    def parseResponse(self, response: str) -> bool:
        self._error = not 'Ok' in response
        return True

    def result(self):
        return None


class CmdGetSerialNumber(Command):
    def __init__(self):
        super().__init__()
        self._error = False
        self.serialNumber = '0000000'

    def commandString(self) -> str:
        return "Read_SN"

    def parseResponse(self, response: str) -> bool:
        if res := parseSerialNumber(response):
            self.serialNumber = res
        else:
            self._error = True
        return True

    def result(self):
        return GuiMessage.SERIAL(self.serialNumber)


class CmdGetLog(Command):
    def __init__(self):
        super().__init__()
        self.serialNumber = '0000000'
        self.lifetimes = 0
        self.log = ""

    def commandString(self) -> str:
        return "Read_LOG"

    def specialParse(self, response: str):
        parts = response.split("\r\n")
        if len(parts) < 4:
            self._error = True
            return

        if not parts[0].startswith("S/N,"):
            self._error = True
            return

        self.serialNumber = parts[0].replace("S/N,", "")

        if not parts[1].startswith("TIME,"):
            self._error = True
            return

        self.lifetimes = int(parts[1].replace("TIME,", ""), 16)

        self.log = parts[2]

        return True

    def parseResponse(self, response: str) -> bool:
        self.specialParse(response)
        return True

        #TODO: questa istruzione ogni tanto causa un errore
        res = parse("S/N,{:d}\r\nTIME,{:x}\r\n{}\r\n",
                    "S/N,00.00,\r\nTIME,0x1400\r\nLOG\r\n")  # response)

        if len(res.fixed) == 3:
            self.serialNumber = str(res[0])
            self.lifetimes = int(res[1])
            self.log = str(res[2])
        else:
            self._error = True
        return True

    def result(self):
        return GuiMessage.LOG(self.serialNumber, self.lifetimes, self.log)


class CmdGetPower(Command):
    def __init__(self):
        super().__init__()
        self.direct = 0
        self.reflected = 0
        self.temp = 0

    def commandString(self) -> str:
        return "Read_PAR"

    def parseResponse(self, response: str) -> bool:
        self.direct, self.reflected, self.temp = parsePar(response)
        return True

    def result(self):
        return GuiMessage.POWER(self.direct, self.reflected, self.temp)


class CmdGetRevision(Command):
    def __init__(self):
        super().__init__()
        self._error = False
        self.revision = ''

    def commandString(self) -> str:
        return "Read_REV"

    def parseResponse(self, response: str) -> bool:
        if 'RM' in response and 'FW' in response:
            self.revision = response.replace('\r\n', '\n')
        else:
            self._error = True
        return True

    def result(self):
        return GuiMessage.REVISION(self.revision)


class CmdGetAttenuation(Command):
    def __init__(self):
        super().__init__()
        self.att = 0

    def commandString(self) -> str:
        return "Read_ATT"

    def parseResponse(self, response: str) -> bool:
        res = parse("ATT,{:F},dB\r\n", response)

        if len(res.fixed) == 1:
            self.att = float(res.fixed[0])
        else:
            self._error = True
        return True

    def result(self):
        return GuiMessage.ATTENUATION(self.att)


class CmdSetAttenuation(CmdSet):
    def __init__(self, attenuation):
        super().__init__()
        self.att = attenuation

    def commandString(self) -> str:
        return "Set_ATT,{:2f}".format(self.att)


class CmdSetOutput(CmdSet):
    def __init__(self, output):
        super().__init__()
        self.out = output

    def commandString(self) -> str:
        return "Set_TOP,{}".format(self.out)


class CmdGetOutput(Command):
    def __init__(self):
        super().__init__()
        self._error = False
        self.pow = 0

    def commandString(self) -> str:
        return "Read_TOP"

    def parseResponse(self, response: str) -> bool:
        res = parse("TOP,{:d},W\r\n", response)

        if len(res.fixed) == 1:
            self.pow = int(res.fixed[0])
        else:
            self._error = True
        return True

    def result(self):
        return GuiMessage.OUTPUT(self.pow)


class CmdSetMode(CmdSet):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self._error = False

    def commandString(self) -> str:
        return "Set_MODE,{}".format(self.mode)

class CmdSetFrequency(CmdSet):
    def __init__(self, freq, hidden=True):
        super().__init__(hidden)
        self.freq = freq
        self._error = False

    def commandString(self) -> str:
        return "Set_FRQ,{}".format(self.freq)



class CmdAny(Command):
    def __init__(self, cmd, hidden=False):
        super().__init__(hidden)
        self.cmd = cmd

    def commandString(self) -> str:
        return self.cmd

    def parseResponse(self, response: str) -> bool:
        return True

    def result(self):
        return None
