import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum
from abc import ABC, abstractmethod
from typing import List

from .serialutils import *
from .view.main import mainWindow
from .resources import resourcePath
from .model import *


class Command(ABC):
    @abstractmethod
    def commandString(self) -> str:
        pass

    @abstractmethod
    def parseResponse(self, response: str) -> bool:
        pass

    @abstractmethod
    def error(self) -> bool:
        pass

    @abstractmethod
    def response(self) -> str:
        pass


class CmdGetSerialNumber(Command):
    def __init__(self):
        self._error = False
        self.serialNumber = '0000000'

    def error(self):
        return self._error

    def commandString(self) -> str:
        return "Read_SN"

    def parseResponse(self, response: str) -> bool:
        if response.startswith('S/N,') and response.endswith('\r\n'):
            self.serialNumber = response.replace(
                'S/N,', '').replace('\r\n', '')
        else:
            self._error = True
        return True

    def response(self):
        return self.serialNumber


class CmdGetPower(Command):
    def __init__(self):
        self._error = False
        self.data = ""

    def error(self):
        return self._error

    def commandString(self) -> str:
        return "Read_PAR"

    def parseResponse(self, response: str) -> bool:

        return True

    def response(self):
        return self.data




class CmdGetRevision(Command):
    def __init__(self):
        self._error = False
        self.revision = ''

    def error(self):
        return self._error

    def commandString(self) -> str:
        return "Read_REV"

    def parseResponse(self, response: str) -> bool:
        if 'RM' in response and 'FW' in response:
            self.revision = response.replace('\r\n', '\n')
        else:
            self._error = True
        return True

    def response(self):
        return self.revision

class CmdSetMode(Command):
    def __init__(self, mode):
        self.mode = mode
        self._error = False

    def error(self):
        return self._error

    def commandString(self) -> str:
        return "Set_MODE,{}".format(self.mode)

    def parseResponse(self, response: str) -> bool:
        self._error = not 'Ok' in response
        return True

    def response(self):
        return ""




class CommandSequence:
    def __init__(self):
        self.index = 0
        self.seq = []
        self.sent = False
        self.packer = lambda x: x

    def newSequence(self, sequence, packer=lambda _ : None):
        self.__init__()
        self.seq = sequence
        self.packer = packer

    def done(self) -> bool:
        return self.index == len(self.seq)

    def next(self):
        if self.done():
            return None
        elif not self.sent:
            self.sent = True
            return self.seq[self.index]
        else:
            return None

    def parse(self, response: str):
        if self.done():
            return True

        if self.seq[self.index].parseResponse(response):
            self.index += 1
            self.sent = False
            return True

    def error(self) -> bool:
        return all([x.error() for x in self.seq]) and len(self.seq) > 0

    def result(self):
        return self.packer([x.response() for x in self.seq])


def controllerTask(guiq: queue.Queue, workq: queue.Queue):
    port: serial.Serial = None
    #cmdq : queue.Queue = queue.Queue()
    commandSequence: CommandSequence = CommandSequence()
    config: SerialConfig = SerialConfig()

    while True:
        try:
            msg: WorkMessage = workq.get(timeout=0.1)

            def newPort(c: SerialConfig):
                nonlocal port
                if c.port:
                    config = c
                    if port:
                        port.close()

                    bytesize = {8: serial.EIGHTBITS}[c.data]
                    parity = {'None': serial.PARITY_NONE,
                              'Even': serial.PARITY_EVEN, 'Odd': serial.PARITY_ODD}[c.parity]
                    stop = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE,
                            2: serial.STOPBITS_TWO}[c.stop]
                    port = serial.Serial(
                        port=c.port, baudrate=c.baud, bytesize=bytesize, parity=parity, stopbits=stop, timeout=0.1)
                else:
                    port = None

            def send(data: str):
                nonlocal port
                if port:
                    port.write(data.encode('ASCII'))

            def getInfo():
                nonlocal commandSequence
                if commandSequence.done():
                    commandSequence.newSequence(
                        [CmdGetSerialNumber(), CmdGetRevision()], lambda l: GuiMessage.INFO(l[0], l[1]))

            def setMode(mode):
                nonlocal commandSequence
                if commandSequence.done():
                    commandSequence.newSequence([CmdSetMode(mode)])


            msg.match(
                newport=newPort,
                send=send,
                getinfo=getInfo,
                mode=setMode,
            )
        except queue.Empty:
            pass

        if port:
            read = port.read(port.in_waiting)

            if read:
                guiq.put(GuiMessage.RECV(read.decode(errors='ignore')))

            if commandSequence:
                cmd: Command = commandSequence.next()
                if cmd:
                    tosend = cmd.commandString() + config.endStr()
                    guiq.put(GuiMessage.SEND(tosend))
                    port.write(tosend.encode())

                if commandSequence.error():
                    commandSequence.newSequence([])
                    guiq.put(GuiMessage.ERROR())

                if read:
                    commandSequence.parse(read.decode(errors='ignore'))

                    if commandSequence.done():
                        res = commandSequence.result()
                        if res:
                            guiq.put(res)
