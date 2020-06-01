import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum
from abc import ABC, abstractmethod
import time
from typing import List
from parse import parse

from .serialutils import *
from .view.main import mainWindow
from .resources import resourcePath
from .model import *


def elapsed(start, delay):
    return time.time() - start > delay

def clearq(q: queue.Queue):
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            pass

class Command(ABC):
    def __init__(self, hidden=False):
        self.start()
        self.hidden = hidden

    def start(self):
        self.started = time.time()

    def timeout(self):
        return elapsed(self.started, 10)

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
    def result(self) -> GuiMessage:
        pass


class CmdGetSerialNumber(Command):
    def __init__(self):
        super().__init__()
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

    def result(self):
        return GuiMessage.SERIAL(self.serialNumber)


class CmdGetPower(Command):
    def __init__(self):
        super().__init__(hidden=True)
        self._error = False

    def error(self):
        return self._error

    def commandString(self) -> str:
        return "Read_PAR"

    def parseResponse(self, response: str) -> bool:
        self.direct, self.reflected, self.temp = parse("PAR,{},Wf,{},Wr,{},C\r\n", response)
        return True

    def result(self):
        return GuiMessage.POWER(self.direct, self.reflected, self.temp)


class CmdGetRevision(Command):
    def __init__(self):
        super().__init__()
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

    def result(self):
        return GuiMessage.REVISION(self.revision)


class CmdSetMode(Command):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self._error = False

    def error(self):
        return self._error

    def commandString(self) -> str:
        return "Set_MODE,{}".format(self.mode)

    def parseResponse(self, response: str) -> bool:
        self._error = not 'Ok' in response
        return True

    def result(self):
        return None

class CmdAny(Command):
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def error(self):
        return False

    def commandString(self) -> str:
        return self.cmd

    def parseResponse(self, response: str) -> bool:
        return True

    def result(self):
        return None



def controllerTask(guiq: queue.Queue, workq: queue.Queue):
    port: serial.Serial = None
    cmdq: queue.Queue = queue.Queue()
    config: SerialConfig = SerialConfig()
    currentCmd = None
    timestamp = time.time()
    error : bool = False

    while True:
        try:
            msg: WorkMessage = workq.get(timeout=0.1)

            def newPort(c: SerialConfig):
                nonlocal port
                nonlocal cmdq
                clearq(cmdq)
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
                nonlocal cmdq
                cmdq.put(CmdAny(data))

            def getInfo():
                nonlocal cmdq
                cmdq.put(CmdGetSerialNumber())
                cmdq.put(CmdGetRevision())

            def setMode(mode):
                nonlocal cmdq
                cmdq.put(CmdSetMode(mode))

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

            if read and not currentCmd.hidden:
                guiq.put(GuiMessage.RECV(read.decode(errors='ignore')))

            if currentCmd:
                if not currentCmd.sent:
                    tosend = currentCmd.commandString() + config.endStr()
                    port.write(tosend.encode())
                    currentCmd.sent = True

                    if not currentCmd.hidden:
                        guiq.put(GuiMessage.SEND(tosend))

                if currentCmd.error() or currentCmd.timeout():
                    guiq.put(GuiMessage.ERROR())
                    clearq(cmdq)
                    error= True
                    currentCmd = None

                if read:
                    if currentCmd.parseResponse(read.decode(errors='ignore')):
                        if result := currentCmd.result():
                            guiq.put(result)

                        error = False
                        currentCmd = None
            else:
                try:
                    currentCmd = cmdq.get_nowait()
                    currentCmd.sent = False
                except queue.Empty:
                    currentCmd = None

            if elapsed(timestamp, 1) and not error:
                cmdq.put(CmdGetPower())
                timestamp = time.time()
