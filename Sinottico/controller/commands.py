from abc import ABC, abstractmethod, abstractstaticmethod
import time
import re

from ..model import *


def parseSerialNumber(string):
    if string.startswith('S/N,') and string.endswith('\r\n'):
        return string.replace('S/N,', '').replace('\r\n', '')
    else:
        return None


def parsePar(string):
    dotnum = "([-+]?\d+(?:\.\d+)?)"
    pattern = "PAR,{0},Wf,{0},Wr,{0},C\r\n".format(dotnum)
    if res := re.match(pattern, string):
        return res.groups()
    else:
        return None


class Command(ABC):
    def __init__(self, hidden=True, ending="\r\n"):
        self.start()
        self.hidden = hidden
        self._error = False
        self._ending = ending

    def end_bytes(self):
        return self._ending.encode()

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

    def result(self) -> GuiMessage:
        pass


class ArduinoTemperature(Command):
    def __init__(self, temperature, hidden=True, ending='\n'):
        super().__init__(hidden=hidden, ending=ending)
        self.temperature = temperature

    def commandString(self):
        return str(self.temperature) + self._ending

    def parseResponse(self, response):
        if not response.startswith("Aggiornato "):
            self._error = True
        try:
            if int(response.replace("Aggiornato ", "")) != self.temperature:
                self._error = True
        except ValueError:
            self._error = True

        return True


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
        return "Read_SN" + self._ending

    def parseResponse(self, response: str) -> bool:
        if res := parseSerialNumber(response):
            self.serialNumber = res
        else:
            self._error = True
        return True

    def result(self):
        return GuiMessage.SERIAL(self.serialNumber)


class CmdGetMode(Command):
    def __init__(self):
        super().__init__()
        self.mode = None

    def commandString(self) -> str:
        return "Read_MODE" + self._ending

    def parseResponse(self, response: str) -> bool:
        if response.startswith("MODE,") and response.endswith("\r\n"):
            self.mode = int(response.replace("MODE,", "").replace("\r\n", ""))
        else:
            self._error = True
        return True

    def result(self):
        return GuiMessage.MODE(self.mode)


class CmdGetLog(Command):
    def __init__(self):
        super().__init__()
        self.serialNumber = '0000000'
        self.lifetimes = 0
        self.log = ""

    def commandString(self) -> str:
        return "Read_LOG" + self._ending

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

    def result(self):
        return GuiMessage.LOG(self.serialNumber, self.lifetimes, self.log)


class CmdGetPower(Command):
    def __init__(self):
        super().__init__()
        self.direct = 0
        self.reflected = 0
        self.temp = 0

    def commandString(self) -> str:
        return "Read_PAR" + self._ending

    def parseResponse(self, response: str) -> bool:
        if res := parsePar(response):
            self.direct, self.reflected, self.temp = res
        return True

    def result(self):
        return GuiMessage.POWER(self.direct, self.reflected, self.temp)


class CmdGetRevision(Command):
    def __init__(self):
        super().__init__()
        self._error = False
        self.revision = ''

    def commandString(self) -> str:
        return "Read_REV" + self._ending

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
        return "Read_ATT" + self._ending

    def parseResponse(self, response: str) -> bool:
        if response.startswith("ATT,") and response.endswith(",dB\r\n"):
            self.att = float(
                response.replace("ATT,", "").replace(",dB\r\n", ""))
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
        return "Set_ATT,{:2f}".format(self.att) + self._ending


class CmdSetOutput(CmdSet):
    def __init__(self, output):
        super().__init__()
        self.out = output

    def commandString(self) -> str:
        return "Set_TOP,{}".format(self.out) + self._ending


class CmdGetOutput(Command):
    def __init__(self):
        super().__init__()
        self._error = False
        self.pow = 0

    def commandString(self) -> str:
        return "Read_TOP" + self._ending

    def parseResponse(self, response: str) -> bool:
        if response.startswith("TOP,") and response.endswith(",W\r\n"):
            self.pow = int(response.replace("TOP,", "").replace(",W\r\n", ""))
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
        return "Set_MODE,{}".format(self.mode) + self._ending


class CmdSetFrequency(CmdSet):
    def __init__(self, freq, hidden=True):
        super().__init__(hidden)
        self.freq = freq
        self._error = False

    def commandString(self) -> str:
        return "Set_FRQ,{}".format(self.freq) + self._ending


class CmdAny(Command):
    def __init__(self, cmd, hidden=False):
        super().__init__(hidden)
        self.cmd = cmd

    def commandString(self) -> str:
        return self.cmd + self._ending

    def parseResponse(self, response: str) -> bool:
        return True

    def result(self):
        return None


class CmdNoReturn(Command):
    def __init__(self, cmd, hidden=False):
        super().__init__(hidden)
        self.cmd = cmd

    def commandString(self) -> str:
        return self.cmd + self._ending

    def parseResponse(self, response: str) -> bool:
        return response == 'Ok' + self._ending

    def result(self):
        return None

