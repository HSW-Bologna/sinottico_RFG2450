from queue import Queue
import queue
from enum import Enum
import PySimpleGUI as sg  # type: ignore
from .settings import settingsWindow
from ..resources import resourcePath
from ..model import *

MODES = {"Modalita' {}".format(v): v for v in range(4)}


class Id(Enum):
    CONNECT = 1
    SETTINGS = 3
    TIMEOUT = 10
    SEND = 11
    END = 12
    INPUT = 13
    LOG = 14
    SN = 2
    INFO = 4
    REVISION = 5
    MODES = 6
    STATUS = 7
    DIRPWR = 8
    REFPWR = 9
    TEMP = 15


def explicit(s):
    return s.replace('\r', '\\r').replace('\n', '\\n\n')


def mainWindow(workq: Queue, guiq: Queue):
    connected: bool = False

    tab1 = [
        [
            sg.Frame("Informazioni",
                     [[sg.Text("Numero di serie: "),
                       sg.Input(key=Id.SN)],
                      [sg.Text("", key=Id.REVISION, size=(40, None))],
                      [sg.Button("Richiedi", key=Id.INFO)]])
        ],
        [
            sg.Frame("Modalita'", [[
                sg.Combo(values=list(MODES.keys()),
                         key=Id.MODES,
                         metadata=lambda x: MODES[x],
                         enable_events=True)
            ]])
        ],
        [
            sg.Frame("Parametri", [
                [
                    sg.Text(
                        "Potenza Diretta (W)", size=(20, 1), pad=(0, (10, 0))),
                    sg.Slider(range=(0, 300),
                              size=(20, 20),
                              orientation='horizontal',
                              key=Id.DIRPWR)
                ],
                [
                    sg.Text(
                        "Potenza Riflessa (W)", size=(20, 1), pad=(0,
                                                                   (10, 0))),
                    sg.Slider(range=(0, 300),
                              size=(20, 20),
                              orientation='horizontal',
                              key=Id.DIRPWR)
                ],
                [sg.Text("SWR: ", pad=(0, (20, 0)))],
                [sg.Text("Temperatura: ", key=Id.TEMP)],
            ])
        ],
    ]

    tab2 = [[]]

    tab3 = [[]]

    tab4 = [
        [sg.Text("Ore di lavoro:")],
    ]

    tab5 = [[sg.Multiline(size=(64, 20), key=Id.LOG, disabled=True)],
            [
                sg.Input(size=(60, None), key=Id.INPUT),
                sg.Button(image_filename=resourcePath('send.png'),
                          bind_return_key=True,
                          key=Id.SEND)
            ]]

    layout = [[
        sg.Button(
            'Impostazioni',
            key=Id.SETTINGS,
        ),
        sg.Button('Connetti', key=Id.CONNECT)
    ],
              [
                  sg.TabGroup([[
                      sg.Tab("Informazioni", tab1),
                      sg.Tab("Acquisizione Dati", tab2),
                      sg.Tab("Calibrazione", tab3),
                      sg.Tab("Verbale", tab4),
                      sg.Tab("Terminale", tab5)
                  ]])
              ],
              [sg.Text("Selezionare una porta e connetersi", key=Id.STATUS)]]

    # Create the Window
    window = sg.Window('Window Title', layout, finalize=True)

    config = SerialConfig()

    window[Id.LOG].Widget.tag_config("send", foreground="blue")

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        window[Id.CONNECT].Update(disabled=(config.port == None))
        [
            window[x].Update(disabled=not connected)
            for x in [Id.SEND, Id.INFO, Id.MODES]
        ]

        event, values = window.read(timeout=0.1)
        if event in (None, 'Cancel'):  # if user closes window or clicks cancel
            break

        if event == Id.SETTINGS:
            config = settingsWindow(config)
            if config.port:
                text = "{} {},{}{}{}".format(config.port, config.baud,
                                             config.data, config.parity[0],
                                             config.stop)
            else:
                text = "Impostazioni"
            window[Id.SETTINGS].Update(text=text)

            while window.read(timeout=0,
                              timeout_key=Id.TIMEOUT)[0] != Id.TIMEOUT:
                pass
        elif event == Id.CONNECT:
            workq.put(WorkMessage.NEWPORT(config))
            window[Id.STATUS].Update("Connesso!")
            connected = True
        elif event == Id.SEND and connected:
            workq.put(WorkMessage.SEND(values[Id.INPUT]))
        elif event == Id.INFO:
            workq.put(WorkMessage.GETINFO())
        elif event == Id.MODES:
            element, value = window[event], values[event]
            workq.put(WorkMessage.MODE(element.metadata(value)))
        elif event == '__TIMEOUT__':
            pass
        else:
            print(event)

        try:
            msg: GuiMessage = guiq.get(timeout=0.1)

            msg.match(
                send=lambda s: window[Id.LOG].update(
                    explicit(s), text_color_for_value="blue", append=True),
                recv=lambda s: window[Id.LOG].update(
                    explicit(s), text_color_for_value="black", append=True),
                serial=lambda x: window[Id.SN].Update(x),
                revision=lambda y: window[Id.REVISION].Update(
                    y.replace('\n', '\t')),
                power=lambda x, y, z: print(x, y, z),
                error=lambda: window[Id.STATUS].Update(
                    "Errore di comunicazione!"))
        except queue.Empty:
            pass

    window.close()
