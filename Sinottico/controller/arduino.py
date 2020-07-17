import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum
import time
from typing import List
from types import SimpleNamespace

from ..utils.serialutils import *
from ..resources import resourcePath
from ..model import *
from .commands import *


def clearq(q: queue.Queue):
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            pass


def controller_arduino_task(guiq: queue.Queue, workq: queue.Queue):
    port: serial.Serial = None
    config: SerialConfig = SerialConfig()

    while True:
        try:
            msg: ArduinoMessage = workq.get(timeout=0.1)

            def send_temperature(temp, port, guiq):
                if not port or not port.isOpen():
                    return 

                cmd = ArduinoTemperature(temp, ending=config.endStr())
                port.write(cmd.commandString().encode())

                read = port.read_until(config.endBytes())
                if len(read) > 0 and cmd.parseResponse(read.decode()):
                    if cmd.error():
                        guiq.put(GuiMessage.ERROR_ARDUINO())
                    elif res := cmd.result():
                        guiq.put(res)
                else:
                    guiq.put(GuiMessage.ERROR_ARDUINO())

            def newPort(c: SerialConfig, guiq):
                nonlocal port
                if c.port:
                    config = c
                    if port:
                        port.close()

                    try:
                        port = connect_to_port(c)
                        guiq.put(GuiMessage.CONNECTED_ARDUINO())
                        send_temperature(25, port, guiq)
                    except serial.SerialException as e:
                        print(e)
                        guiq.put(GuiMessage.DISCONNECTED_ARDUINO())

                else:
                    port = None



            msg.match(
                newport=lambda c: newPort(c, guiq),
                temperature=lambda x: send_temperature(x, port, guiq),
            )
        except queue.Empty:
            pass
