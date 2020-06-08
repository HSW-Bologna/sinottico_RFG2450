import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum
import time
from typing import List

from ..serialutils import *
from ..resources import resourcePath
from ..model import *
from .commands import *


def elapsed(start, delay):
    return time.time() - start > delay


def clearq(q: queue.Queue):
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            pass


def controllerTask(guiq: queue.Queue, workq: queue.Queue):
    port: serial.Serial = None
    cmdq: queue.Queue = queue.Queue()
    config: SerialConfig = SerialConfig()
    currentCmd = None
    error: bool = False
    timestamp = 0
    lastmsgts = 0

    selectedTab: int = 0
    mode: int = 0

    while True:
        try:
            msg: WorkMessage = workq.get(timeout=0.1)

            def newPort(c: SerialConfig):
                nonlocal port, cmdq, guiq, timestamp
                clearq(cmdq)
                if c.port:
                    config = c
                    if port:
                        port.close()

                    bytesize = {8: serial.EIGHTBITS}[c.data]
                    parity = {
                        'None': serial.PARITY_NONE,
                        'Even': serial.PARITY_EVEN,
                        'Odd': serial.PARITY_ODD
                    }[c.parity]
                    stop = {
                        1: serial.STOPBITS_ONE,
                        1.5: serial.STOPBITS_ONE_POINT_FIVE,
                        2: serial.STOPBITS_TWO
                    }[c.stop]
                    try:
                        port = serial.Serial(port=c.port,
                                             baudrate=c.baud,
                                             bytesize=bytesize,
                                             parity=parity,
                                             stopbits=stop,
                                             timeout=0.1)
                        guiq.put(GuiMessage.CONNECTED())
                        #cmdq.put(CmdGetLog())
                    except:
                        guiq.put(GuiMessage.DISCONNECTED())

                else:
                    port = None

            def getInfo():
                nonlocal cmdq
                cmdq.put(CmdGetSerialNumber())
                cmdq.put(CmdGetRevision())

            def setTab(x):
                nonlocal selectedTab
                selectedTab = x

            def setMode(cmdq, x):
                nonlocal mode
                mode = x
                cmdq.put(CmdSetMode(x))

                if x == 0:
                    cmdq.put(CmdSetAttenuation(32.00))
                    print("att")
                    cmdq.put(CmdGetAttenuation())
                elif x == 2:
                    cmdq.put(CmdSetOutput(0))

                cmdq.put(CmdGetMode())

            def getLog():
                nonlocal cmdq
                cmdq.put(CmdGetLog())

            def handshake(cmdq):
                cmdq.put(CmdSetMode(0))
                cmdq.put(CmdSetAttenuation(32.00))
                print("att2")
                cmdq.put(CmdGetAttenuation())
                cmdq.put(CmdSetOutput(0))
                cmdq.put(CmdGetOutput())
                cmdq.put(CmdGetMode())
                cmdq.put(CmdGetSerialNumber())
                cmdq.put(CmdGetRevision())

            msg.match(
                newport=newPort,
                send=lambda x: cmdq.put(CmdAny(x)),
                getinfo=getInfo,
                mode=lambda x: setMode(cmdq, x),
                att=lambda x: cmdq.put(CmdSetAttenuation(x)),
                output=lambda x: cmdq.put(CmdSetOutput(x)),
                log=getLog,
                selectedTab=setTab,
                setfreq=lambda x: cmdq.put(CmdSetFrequency(x, hidden=False)),
                handshake=lambda: handshake(cmdq),
            )
        except queue.Empty:
            pass

        if not port:
            continue

        if currentCmd:
            if currentCmd.tosend and elapsed(lastmsgts, 0.05):
                tosend = currentCmd.commandString() + config.endStr()
                currentCmd.start()

                try:
                    port.write(tosend.encode())
                except (OSError, serial.SerialException):
                    guiq.put(GuiMessage.DISCONNECTED())
                    port.close()
                    port = None
                    continue

                currentCmd.tosend = False
                lastmsgts = time.time()

                if not currentCmd.hidden:
                    guiq.put(GuiMessage.SEND(tosend))

            try:
                read = port.read(port.in_waiting)
            except (OSError, serial.SerialException):
                guiq.put(GuiMessage.DISCONNECTED())
                port.close()
                port = None
                continue

            if read and not currentCmd.hidden:
                guiq.put(GuiMessage.RECV(read.decode(errors='ignore')))

            if not currentCmd.tosend and currentCmd.timeout():
                currentCmd.attempts += 1
                if currentCmd.attempts < 5:
                    currentCmd.tosend = True
                else:
                    currentCmd._error = True

            if currentCmd.error():
                guiq.put(GuiMessage.ERROR())
                clearq(cmdq)
                error = True
                currentCmd = None
            elif read:
                if currentCmd.parseResponse(read.decode(errors='ignore')):
                    if result := currentCmd.result():
                        guiq.put(result)

                    error = False
                    currentCmd = None
        else:
            try:
                currentCmd = cmdq.get_nowait()
                currentCmd.tosend = True
                currentCmd.attempts = 0

            except queue.Empty:
                currentCmd = None

        #TODO: sposta questi messaggi nella view
        if elapsed(timestamp, 2) and not error:
            if selectedTab == 1:
                cmdq.put(CmdGetPower())

            if mode == 1:
                cmdq.put(CmdGetAttenuation())
            elif mode == 3:
                cmdq.put(CmdGetOutput())

            timestamp = time.time()
