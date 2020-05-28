import sys
import serial  # type: ignore
import os
import queue
import threading
from enum import Enum

from .serialutils import *
from .view.main import mainWindow
from .resources import resourcePath
from .model import *

def controllerTask(guiq: queue.Queue, workq: queue.Queue):
    port: serial.Serial = None

    while True:
        try:
            msg: WorkMessage = workq.get(timeout=0.1)

            def newPort(c: SerialConfig):
                nonlocal port
                print("connecting to {}".format(c.port))
                if c.port:
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
                print("connected to {}".format(port))

            def send(data: str):
                nonlocal port
                if port:
                    port.write(data.encode('ASCII'))

            msg.match(
                newport=newPort,
                send=send,
            )
        except queue.Empty:
            pass

        if port:
            read = port.read(port.in_waiting)
            if read:
                guiq.put(GuiMessage.RECV(read.decode('ASCII')))


