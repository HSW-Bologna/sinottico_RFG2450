import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum
import time
from typing import List
from dataclasses import dataclass
from multiprocessing import Pool


from ..utils.serialutils import *
from ..resources import resourcePath
from ..model import *
from .commands import *
from .power import launch_find_best_combinations_direct, launch_find_best_combinations_reflex, save_parameters


@dataclass
class Model:
    port: serial.Serial
    cmdq: queue.Queue
    config: SerialConfig
    lastmsgts: float
    mode: int


def elapsed(start, delay):
    return time.time() - start > delay


def clearq(q: queue.Queue):
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            pass


def controllerTask(guiq: queue.Queue, workq: queue.Queue):
    model: Model = Model(port=None, cmdq=queue.Queue(),
                         config=SerialConfig(), lastmsgts=0, mode=0)

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
                        time.sleep(0.05)  # aspetta una risposta
                        # read = port.read_until(cmd.end_bytes()) # alcuni comandi prevedono due righe di risposta
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
                            print(read)
                            guiq.put(GuiMessage.ERROR(
                                "Errore di comunicazione"))
                        elif res := cmd.result():
                            guiq.put(res)
                            return
                        else:
                            return
                    else:
                        guiq.put(GuiMessage.ERROR("Errore di comunicazione"))

                    count += 1
                return

            def newPort(c: SerialConfig):
                nonlocal model, guiq
                clearq(model.cmdq)
                if c.port:
                    model.config = c
                    if model.port:
                        model.port.close()

                    try:
                        model.port = connect_to_port(c)
                        guiq.put(GuiMessage.CONNECTED_RFG())
                        # cmdq.put(CmdGetLog())
                    except:
                        guiq.put(GuiMessage.DISCONNECTED_RFG())

                else:
                    model.port = None

            def getInfo():
                nonlocal model
                model.cmdq.put(CmdGetSerialNumber())
                model.cmdq.put(CmdGetRevision())

            def setMode(cmdq, x):
                nonlocal model
                model.mode = x
                cmdq.put(CmdSetMode(x))

                if x == 0:
                    cmdq.put(CmdSetAttenuation(32.00))
                    cmdq.put(CmdGetAttenuation())
                elif x == 2:
                    cmdq.put(CmdSetOutput(0))

                cmdq.put(CmdGetMode())

            def get_log(m):
                m.cmdq.put(CmdGetLog())

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

            def send_pars(cmdq : queue.Queue, t1 : Tuple[int,int,int,int], t2 : Tuple[int,int,int,int]):
                cmdq.put(CmdNoReturn('assistenza_rm_italy', hidden=True))
                cmdq.put(CmdNoReturn('Set_FWD,{},{},{},{}'.format(t1[0], t1[1], t1[2], t1[3]), hidden=True))
                cmdq.put(CmdNoReturn('Set_REF,{},{},{},{}'.format(t2[0], t2[1], t2[2], t2[3]), hidden=True))

            msg.match(
                newport=newPort,
                send=lambda x: model.cmdq.put(CmdAny(x)),
                getinfo=getInfo,
                mode=lambda x: setMode(model.cmdq, x),
                att=lambda x: model.cmdq.put(CmdSetAttenuation(x)),
                getatt=lambda: model.cmdq.put(CmdGetAttenuation()),
                output=lambda x: model.cmdq.put(CmdSetOutput(x)),
                getoutput=lambda: model.cmdq.put(CmdGetOutput()),
                log=lambda: get_log(model),
                setfreq=lambda x: model.cmdq.put(
                    CmdSetFrequency(x, hidden=False)),
                handshake=lambda: handshake(model.cmdq),
                getpower=lambda: model.cmdq.put(CmdGetPower()),
                find_direct_combinations=lambda x: launch_find_best_combinations_direct(
                    x, guiq),
                find_reflex_combinations=lambda pars, x: launch_find_best_combinations_reflex(pars,
                                                                                              x, guiq),
                save_parameters=lambda src, dst, par1, par2: save_parameters(
                    src, dst, par1, par2, guiq),
                send_parameters=lambda par1, par2: send_pars(model.cmdq, par1, par2),
            )
        except queue.Empty:
            pass

        if not model.port:
            continue
        elif not model.port.isOpen():
            try:
                model.port.open()
                guiq.put(GuiMessage.RECONNECTED())
                clearq(model.cmdq)
            except serial.SerialException:
                continue

        if elapsed(model.lastmsgts, 0.05):
            try:
                cmd = model.cmdq.get_nowait()
                cmd._ending = model.config.endStr()
                send_command(cmd, model.port, guiq)
                model.lastmsgts = time.time()
            except queue.Empty:
                pass
