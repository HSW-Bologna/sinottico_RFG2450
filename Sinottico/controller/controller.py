import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum
import time
from typing import List

from ..serialutils import *
from ..view.main import mainWindow
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
    error : bool = False
    timestamp = time.time()

    selectedTab : int = 0
    mode : int = 0

    while True:
        try:
            msg: WorkMessage = workq.get(timeout=0.1)

            def newPort(c: SerialConfig):
                nonlocal port, cmdq, guiq
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
                    try:
                        port = serial.Serial(
                            port=c.port, baudrate=c.baud, bytesize=bytesize, parity=parity, stopbits=stop, timeout=0.1)
                        guiq.put(GuiMessage.CONNECTED())
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

            def setMode(x):
                nonlocal mode, cmdq
                mode = x
                cmdq.put(CmdSetMode(x))

            msg.match(
                newport=newPort,
                send=lambda x: cmdq.put(CmdAny(x)),
                getinfo=getInfo,
                mode=setMode,
                att=lambda x : cmdq.put(CmdSetAttenuation(x)),
                output=lambda x : cmdq.put(CmdSetOutput(x)),
                log=lambda : cmdq.put(CmdGetLog()),
                selectedTab=setTab,
            )
        except queue.Empty:
            pass

        if port:
            try:
                read = port.read(port.in_waiting)
            except OSError:
                guiq.put(GuiMessage.DISCONNECTED())
                port.close()
                port = None

            if currentCmd:
                if read and not currentCmd.hidden:
                    guiq.put(GuiMessage.RECV(read.decode(errors='ignore')))
                    
                if not currentCmd.sent:
                    tosend = currentCmd.commandString() + config.endStr()
                    port.write(tosend.encode())
                    currentCmd.sent = True

                    if not currentCmd.hidden:
                        guiq.put(GuiMessage.SEND(tosend))

                if currentCmd.error() or currentCmd.timeout():
                    print(type(currentCmd))
                    guiq.put(GuiMessage.ERROR())
                    clearq(cmdq)
                    error= True
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
                    currentCmd.sent = False
                except queue.Empty:
                    currentCmd = None

            if elapsed(timestamp, 4) and not error:
                if selectedTab == 1:
                    cmdq.put(CmdGetPower())

                if mode == 1:
                    cmdq.put(CmdGetAttenuation())
                elif mode == 3:
                    cmdq.put(CmdGetOutput())                
                
                timestamp = time.time()
