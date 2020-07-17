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


# FIXME: Questo task e' strutturato male. Il suo unico scopo e' mandare messaggi, quindi non ha senso che
# intervalli nel ciclo la lettura della porta: quando invia un messaggio si puo' bloccare nell'aspettare la risposta.
# cmdq ci puo' stare nell'ottica di organizzazione dei dati, ma basterebbe una funzione invia_comandi


def controllerTask(guiq: queue.Queue, workq: queue.Queue):
    port: serial.Serial = None
    cmdq: queue.Queue = queue.Queue()
    config: SerialConfig = SerialConfig()
    currentCmd = None
    error: bool = False
    lastmsgts = 0

    mode: int = 0

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
                cmdq.put(CmdSetMode(0))
                cmdq.put(CmdSetAttenuation(32.00))
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

        if currentCmd:
            if currentCmd.tosend and elapsed(lastmsgts, 0.05):
                tosend = currentCmd.commandString() + config.endStr()
                currentCmd.start()

                try:
                    port.write(tosend.encode())
                except (OSError, serial.SerialException):
                    guiq.put(GuiMessage.DISCONNECTED_RFG())
                    port.close()
                    continue

                currentCmd.tosend = False
                lastmsgts = time.time()

                if not currentCmd.hidden:
                    guiq.put(GuiMessage.SEND(tosend))

            try:
                read = port.read(port.in_waiting)
            except (OSError, serial.SerialException):
                guiq.put(GuiMessage.DISCONNECTED_RFG())
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

            if currentCmd.error(
            ):  #TODO: questo probabilmente andrebbe spostato sotto...
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
