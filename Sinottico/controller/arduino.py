import sys
import serial
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
from .commands import ArduinoTemperature


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

            def send_command(cmd, port, guiq):
                if not port or not port.isOpen():
                    return

                counter = 0
                while counter < 5:
                    try:
                        time.sleep(.5)
                        tosend = cmd.commandString().encode()
                        port.reset_input_buffer()
                        port.write(tosend)
                        read = port.read_until(cmd.end_bytes())
                    except serial.SerialException as e:
                        port.close()
                        guiq.put(GuiMessage.DISCONNECTED_ARDUINO())
                        return

                    if len(read) > 0 and cmd.parseResponse(read.decode(errors='ignore')):
                        if cmd.error():
                            pass
                        else:
                            if res := cmd.result():
                                guiq.put(res)
                            return

                    counter += 1

                guiq.put(GuiMessage.ERROR_ARDUINO())

            def newPort(c: SerialConfig, guiq):
                nonlocal port
                if c.port:
                    config = c
                    if port:
                        port.close()

                    try:
                        port = connect_to_port(c, .5)
                        time.sleep(2)
                        guiq.put(GuiMessage.CONNECTED_ARDUINO())
                        send_command(
                            ArduinoTemperature(25, ending=config.endStr()),
                            port, guiq)
                    except serial.SerialException as e:
                        print(e)
                        guiq.put(GuiMessage.DISCONNECTED_ARDUINO())

                else:
                    port = None

            msg.match(
                newport=lambda c: newPort(c, guiq),
                temperature=lambda x: send_command(ArduinoTemperature(x, ending=config.endStr()), port,
                                                   guiq),
            )
        except queue.Empty:
            pass

        if port and not port.isOpen():
            print("chiusa")
            try:
                port.open()
                guiq.put(GuiMessage.CONNECTED_ARDUINO())
            except serial.SerialException:
                continue
