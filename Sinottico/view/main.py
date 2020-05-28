from queue import Queue
import queue
from enum import Enum
import PySimpleGUI as sg  # type: ignore
from .settings import settingsWindow
from ..resources import resourcePath
from ..model import *

class Id(Enum):
    CONNECT = 1
    SETTINGS = 3
    TIMEOUT = 10
    SEND = 11
    END = 12
    INPUT = 13
    LOG = 14

def explicit(s):
    return s.replace('\r', '\\r').replace('\n', '\\n')

def mainWindow(workq : Queue, guiq : Queue):
    connected: bool = False

    layout = [[sg.Button('Impostazioni', key=Id.SETTINGS,), sg.Button('Connetti', key=Id.CONNECT)],
              [sg.Multiline(size=(40, 20), key=Id.LOG)],
              [sg.Input(size=(40, None), key=Id.INPUT), sg.Button(image_filename=resourcePath('send.png'), bind_return_key=True, key=Id.SEND)]]

    # Create the Window
    window = sg.Window('Window Title', layout, finalize=True)

    config = SerialConfig()

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        window[Id.CONNECT].Update(disabled=(config.port == None))
        window[Id.SEND].Update(disabled=not connected)

        event, values = window.read(timeout=0.1)
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            break

        if event == Id.SETTINGS:
            config = settingsWindow(config)
            if config.port:
                text = "{} {},{}{}{}".format(
                    config.port, config.baud, config.data, config.parity[0], config.stop)
            else:
                text = "Impostazioni"
            window[Id.SETTINGS].Update(text=text)

            while window.read(timeout=0, timeout_key=Id.TIMEOUT)[0] != Id.TIMEOUT:
                pass
        elif event == Id.CONNECT:
            workq.put(WorkMessage.NEWPORT(config))
            connected = True
        elif event == Id.SEND and connected:
            end = {"Niente": "", "CR": "\r",
                   "LF": "\n", "CR+LF": "\r\n"}[config.end]
            window[Id.LOG].print(values[Id.INPUT] + explicit(end))
            workq.put(WorkMessage.SEND(values[Id.INPUT] + end))
        elif event == '__TIMEOUT__':
            pass
        else:
            print(event)

        try:
            msg: GuiMessage = guiq.get(timeout=0.1)

            msg.match(recv=lambda s: window[Id.LOG].print(explicit(s)))
        except queue.Empty:
            pass

    window.close()
