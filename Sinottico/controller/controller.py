import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum
import time
from typing import List

from ..utils.serialutils import *
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
    lastmsgts: float = 0

    mode: int = 0

    while True:
        try:
            msg: WorkMessage = workq.get(timeout=0.1)

            def send_command(cmd, port, guiq):
                if not port or not port.isOpen():
                    return

                count = 0
                while count < 5:
                    try:
                        tosend = cmd.commandString().encode()
                        if not cmd.hidden:
                            guiq.put(GuiMessage.SEND(tosend.decode()))
                        port.write(tosend)
                        time.sleep(0.02)  # aspetta una risposta
                        #read = port.read_until(cmd.end_bytes()) # alcuni comandi prevedono due righe di risposta
                        read = port.read(port.in_waiting)
                    except serial.SerialException as e:
                        port.close()
                        guiq.put(GuiMessage.DISCONNECTED_RFG())
                        return

                    if len(read) > 0 and cmd.parseResponse(
                            read.decode(errors='ignore')):

                        if not cmd.hidden:
                            guiq.put(
                                GuiMessage.RECV(read.decode(errors='ignore')))

                        if cmd.error():
                            guiq.put(GuiMessage.ERROR())
                        elif res := cmd.result():
                            guiq.put(res)
                            return
                        else:
                            return
                    else:
                        guiq.put(GuiMessage.ERROR())

                    count += 1
                return

            def newPort(c: SerialConfig):
                nonlocal port, cmdq, guiq
                clearq(cmdq)
                if c.port:
                    config = c
                    if port:
                        port.close()

                    try:
                        port = connect_to_port(c)
                        guiq.put(GuiMessage.CONNECTED_RFG())
                        #cmdq.put(CmdGetLog())
                    except:
                        guiq.put(GuiMessage.DISCONNECTED_RFG())

                else:
                    port = None

            def getInfo():
                nonlocal cmdq
                cmdq.put(CmdGetSerialNumber())
                cmdq.put(CmdGetRevision())

            def setMode(cmdq, x):
                nonlocal mode
                mode = x
                cmdq.put(CmdSetMode(x))

                if x == 0:
                    cmdq.put(CmdSetAttenuation(32.00))
                    cmdq.put(CmdGetAttenuation())
                elif x == 2:
                    cmdq.put(CmdSetOutput(0))

                cmdq.put(CmdGetMode())

            def getLog():
                nonlocal cmdq
                cmdq.put(CmdGetLog())

            def handshake(cmdq):
                cmdq.put(CmdSetMode(2))
                cmdq.put(CmdSetOutput(0))
                cmdq.put(CmdSetMode(0))
                cmdq.put(CmdSetAttenuation(32.00))
                cmdq.put(CmdGetAttenuation())
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
                getatt=lambda: cmdq.put(CmdGetAttenuation()),
                output=lambda x: cmdq.put(CmdSetOutput(x)),
                getoutput=lambda: cmdq.put(CmdGetOutput()),
                log=getLog,
                setfreq=lambda x: cmdq.put(CmdSetFrequency(x, hidden=False)),
                handshake=lambda: handshake(cmdq),
                getpower=lambda: cmdq.put(CmdGetPower()),
            )
        except queue.Empty:
            pass

        if not port:
            continue
        elif not port.isOpen():
            try:
                port.open()
                guiq.put(GuiMessage.RECONNECTED())
                clearq(cmdq)
                currentCmd = None
            except serial.SerialException:
                continue

        if elapsed(lastmsgts, 0.05):
            try:
                cmd = cmdq.get_nowait()
                cmd._ending = config.endStr()
                send_command(cmd, port, guiq)
                lastmsgts = time.time()
            except queue.Empty:
                pass