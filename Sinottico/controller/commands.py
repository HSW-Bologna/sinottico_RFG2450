from abc import ABC, abstractmethod
from parse import parse  # type: ignore
import time

from ..model import *


class Command(ABC):
    def __init__(self, hidden=False):
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
        if response.startswith('S/N,') and response.endswith('\r\n'):
            self.serialNumber = response.replace('S/N,',
                                                 '').replace('\r\n', '')
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

    def parseResponse(self, response: str) -> bool:
        res = parse("S/N,{:d}\r\nTIME,{:x}\r\n{}\r\n", response)

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
        super().__init__(hidden=True)
        self._error = False

    def commandString(self) -> str:
        return "Read_PAR"

    def parseResponse(self, response: str) -> bool:
        self.direct, self.reflected, self.temp = parse(
            "PAR,{},Wf,{},Wr,{},C\r\n", response)
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
    def __init__(self, hidden=True):
        super().__init__(hidden)
        self._error = False
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
    def __init__(self, attenuation, hidden=True):
        super().__init__(hidden)
        self.att = attenuation

    def commandString(self) -> str:
        return "Set_ATT,{:2f}".format(self.att)


class CmdSetOutput(CmdSet):
    def __init__(self, output, hidden=True):
        super().__init__(hidden)
        self.out = output

    def commandString(self) -> str:
        return "Set_TOP,{}".format(self.out)


class CmdGetOutput(Command):
    def __init__(self, hidden=True):
        super().__init__(hidden)
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


class CmdAny(Command):
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def commandString(self) -> str:
        return self.cmd

    def parseResponse(self, response: str) -> bool:
        return True

    def result(self):
        return None
