from queue import Queue
import queue
from enum import Enum, auto
import time
import re
import PySimpleGUI as sg  # type: ignore
from types import SimpleNamespace

from ..popups import validate_float_lask
from ..settings import settings_window
from ...resources import resourcePath
from ...model import *
from .elements import Id
from .test_procedure import automatedTestProcedure

MODES = {"Modalita' {}".format(v): v for v in range(4)}


def explicit(s):
    return s.replace('\r', '\\r').replace('\n', '\\n\n')


def updateWidgets(m, window, c, carduino):
    window[Id.CONNECT].Update(disabled=not c.port)
    window[Id.CONNECT_ARDUINO].Update(disabled=not carduino.port)
    [
        window[x].Update(disabled=not m.connected) for x in [
            Id.SEND,
            Id.INFO,
            Id.TAB1,
            Id.TAB2,
            Id.TAB3,
            Id.TAB4,
            Id.TAB5,
        ]
    ]
    [
        window[x].Update(
            disabled=not (window[Id.TEMPLATE].Get()
                          and window[Id.DESTINATION].Get() and m.connected))
        for x in [Id.AUTOTEST, Id.RETRYAUTOTEST]
    ]


def calculateVSWR(pref, pfwr):
    import math
    if pfwr == 0:
        return None
    elif 1 - math.sqrt(pref / pfwr) == 0:
        return None
    else:
        return (1 + math.sqrt(pref / pfwr)) / (1 - math.sqrt(pref / pfwr))


def startAutomatedTest(m, w, template, destination):
    elements = [
        Id.SETTINGS, Id.CONNECT, Id.CONNECT_ARDUINO, Id.TAB1, Id.TAB3, Id.TAB4,
        Id.TAB5, Id.AUTOTEST, Id.RETRYAUTOTEST, Id.TEMP_HIGH, Id.TEMP_LOW, Id.K
    ]
    [w[x].Update(disabled=True) for x in elements]
    w[Id.TAB2].Select()
    try:
        temp_bassa = int(w[Id.TEMP_LOW].Get())
        temp_alta = int(w[Id.TEMP_HIGH].Get())
    except ValueError:
        temp_bassa = 23
        temp_alta = 43
    m.data_acquisition = automatedTestProcedure(m, w, template, destination,
                                                temp_bassa, temp_alta)
    [w[x].Update(disabled=False) for x in elements]


def selectMode(w, mode):
    revmodes = {v: k for k, v in MODES.items()}
    modes = [Id.TABMODE1, Id.TABMODE2, Id.TABMODE3, Id.TABMODE4]
    [w[x].Update(disabled=True) for x in modes]
    w[modes[mode]].Update(disabled=False)
    w[modes[mode]].Select()
    w[Id.MODES].Update(value=revmodes[mode])


def mainWindow(workq: Queue, ardq: Queue, guiq: Queue):
    sg.theme("DefaultNoMoreNagging")
    oldkvalue = ""
    m: SimpleNamespace = SimpleNamespace(connected=False,
                                         mode=0,
                                         timestamp=0,
                                         tab=0,
                                         collectedData=None,
                                         workq=workq,
                                         ardq=ardq,
                                         guiq=guiq,
                                         restart=False,
                                         arudino_connected=False,
                                         data_acquisition=False)

    tab1 = [
        [
            sg.Frame("Informazioni",
                     [[sg.Sizer(500, 0)],
                      [sg.Text("Numero di serie: "),
                       sg.Input(key=Id.SN)],
                      [sg.Text("", key=Id.REVISION, size=(40, None))],
                      [sg.Button("Richiedi", key=Id.INFO)]],
                     pad=(0, 10))
        ],
        [
            sg.Frame("Modalita'", [
                [
                    sg.Combo(list(MODES.keys()),
                             key=Id.MODES,
                             enable_events=True,
                             size=(20, 1),
                             readonly=True)
                ],
                [
                    sg.TabGroup([[
                        sg.Tab("", [[sg.Sizer(500, 0)],
                                    [
                                        sg.Sizer(0, 80),
                                        sg.Text("Attenuazione: 0.00",
                                                size=(20, 1),
                                                key=Id.ATTLBL),
                                        sg.Slider(range=(0, 3200),
                                                  resolution=25,
                                                  disable_number_display=True,
                                                  tooltip="Attenuazione",
                                                  orientation="horizontal",
                                                  enable_events=True,
                                                  key=Id.DIGATT)
                                    ]],
                               key=Id.TABMODE1,
                               disabled=True,
                               visible=False),
                        sg.Tab("", [[
                            sg.Sizer(0, 80),
                            sg.Text("Attenuazione: ", key=Id.ATT, size=(32, 1))
                        ]],
                               key=Id.TABMODE2,
                               disabled=True,
                               visible=False),
                        sg.Tab("", [[
                            sg.Sizer(0, 80),
                            sg.Text(
                                "Potenza: 0 W", size=(20, 1), key=Id.POWLBL),
                            sg.Slider(range=(0, 300),
                                      orientation="horizontal",
                                      enable_events=True,
                                      disable_number_display=True,
                                      key=Id.DIGPOW)
                        ]],
                               key=Id.TABMODE3,
                               disabled=True,
                               visible=False),
                        sg.Tab("", [[
                            sg.Sizer(0, 80),
                            sg.Text("Potenza: ", key=Id.POW, size=(32, 1))
                        ]],
                               key=Id.TABMODE4,
                               disabled=True,
                               visible=False),
                    ]],
                                pad=(0, 20))
                ],
            ]),
        ],
        [
            sg.Frame("Parametri", [
                [sg.Sizer(500, 0)],
                [sg.Text("Potenza diretta:", key=Id.DIRPWR, size=(32, 1))],
                [sg.Text("Potenza riflessa:", key=Id.REFPWR, size=(32, 1))],
                [
                    sg.Text("Temperatura: ", size=(24, 1), key=Id.TEMP),
                    sg.Text("VSWR: ", size=(12, 1), key=Id.SWR),
                ],
            ],
                     pad=(0, 20))
        ],
    ]

    tab2: List[List[sg.Element]] = [
        [
            sg.Input("", size=(48, 1), key=Id.TEMPLATE),
            sg.FileBrowse("Template",
                          file_types=(('Excel files', "*.xlsx"), ),
                          size=(16, 1),
                          key=Id.TEMPBTN),
        ],
        [
            sg.Input("", size=(48, 1), key=Id.DESTINATION),
            sg.FolderBrowse("Destinazione", size=(16, 1), key=Id.DESTBTN),
        ],
        [
            sg.Spin(["{:.2f}".format(x / 100.) for x in range(5, 155, 5)],
                    initial_value="1.00",
                    change_submits=True,
                    size=(5, 1),
                    key=Id.K),
            sg.Text("Coefficiente K", size=(16, 1)),
        ],
        [
            sg.Spin([x for x in range(1, 80)],
                    initial_value="23",
                    change_submits=True,
                    size=(5, 1),
                    key=Id.TEMP_LOW),
            sg.Text("Temperatura bassa", size=(25, 1)),
            sg.Spin([x for x in range(1, 80)],
                    initial_value="43",
                    change_submits=True,
                    size=(5, 1),
                    key=Id.TEMP_HIGH),
            sg.Text("Temperatura alta", size=(25, 1)),
        ],
        [
            sg.Button("Avvio Procedura", key=Id.AUTOTEST),
            sg.Button("Riprendi", key=Id.RETRYAUTOTEST)
        ],
        [
            sg.Multiline(disabled=True,
                         autoscroll=True,
                         key=Id.LOGAUTO,
                         size=(68, 15))
        ],
    ]

    tab3: List[List[sg.Element]] = [[]]

    tab4 = [
        [sg.Text("Ore di lavoro:", size=(40, 1), key=Id.LOGHOURS)],
        [sg.Multiline(size=(68, 20), disabled=True, key=Id.LOGLOG)],
    ]

    tab5 = [[
        sg.Multiline(size=(68, 20), key=Id.LOG, autoscroll=True, disabled=True)
    ],
            [
                sg.Input(size=(64, None), key=Id.INPUT),
                sg.Button(image_filename=resourcePath('send.png'),
                          bind_return_key=True,
                          key=Id.SEND)
            ]]

    layout = [[
        sg.Button(
            'Impostazioni',
            key=Id.SETTINGS,
        ),
        sg.Button('Connetti', key=Id.CONNECT),
        sg.Text('RFG2450', key=Id.CONNECT_STATUS1, size=(32, 1)),
    ],
              [
                  sg.Button(
                      'Impostazioni',
                      key=Id.SETTINGS_ARDUINO,
                  ),
                  sg.Button('Connetti', key=Id.CONNECT_ARDUINO),
                  sg.Text('Arduino', key=Id.CONNECT_STATUS2, size=(32, 1)),
              ],
              [
                  sg.TabGroup([[
                      sg.Tab("Informazioni", tab1, key=Id.TAB1),
                      sg.Tab("Acquisizione Dati", tab2, key=Id.TAB2),
                      sg.Tab("Calibrazione", tab3, key=Id.TAB3),
                      sg.Tab("Verbale", tab4, key=Id.TAB4),
                      sg.Tab("Terminale", tab5, key=Id.TAB5)
                  ]],
                              key=Id.MAINTAB,
                              enable_events=True)
              ],
              [
                  sg.Text("Selezionare una porta e connettersi",
                          key=Id.STATUS,
                          size=(64, 1))
              ]]

    # Create the Window
    window = sg.Window('Collaudo RFG2450',
                       layout,
                       finalize=True,
                       return_keyboard_events=True)

    config = SerialConfig()
    config_arduino = SerialConfig(end="LF")

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        updateWidgets(m, window, config, config_arduino)

        event, values = window.read(timeout=0.1, timeout_key=Id.TIMEOUT)
        if event in (None, 'Cancel'):  # if user closes window or clicks cancel
            break

        if (newvalue := validate_float_lask(window[Id.K].Get(),
                                            window[Id.K])) != None:
            oldkvalue = newvalue
        else:
            window[Id.K].Update(oldkvalue)

        for x in [Id.TEMP_LOW, Id.TEMP_HIGH]:
            raw = window[x].Get()
            window[x].Update(re.sub("[^0-9]", "", raw))

        if event in [Id.SETTINGS, Id.SETTINGS_ARDUINO]:
            configs = {
                Id.SETTINGS: config,
                Id.SETTINGS_ARDUINO: config_arduino
            }
            c = configs[event]
            otherc = configs[{Id.SETTINGS : Id.SETTINGS_ARDUINO, Id.SETTINGS_ARDUINO : Id.SETTINGS}[event]]
            c.set_to(settings_window(c, avoid=[otherc.port]))
            if c.port:
                text = "{} {},{}{}{}".format(c.port, c.baud, c.data,
                                             c.parity[0], c.stop)
            else:
                text = "Impostazioni"
            window[event].Update(text=text)

            while window.read(timeout=0,
                              timeout_key=Id.TIMEOUT)[0] != Id.TIMEOUT:
                pass
        elif event == Id.CONNECT:
            m.workq.put(WorkMessage.NEWPORT(config))
        elif event == Id.CONNECT_ARDUINO:
            m.ardq.put(ArduinoMessage.NEWPORT(config_arduino))
        elif event == Id.SEND:
            m.workq.put(WorkMessage.SEND(values[Id.INPUT]))
        elif event == Id.INFO:
            m.workq.put(WorkMessage.GETINFO())
        elif event == Id.MODES:
            element, value = window[event], values[event]
            m.workq.put(WorkMessage.MODE(MODES[value]))
        elif event == Id.TIMEOUT:
            pass
        elif event == Id.DIGATT:
            value = values[event] / 100.
            window[Id.ATTLBL].Update("Attenuazione: {:.2f}".format(value))
            m.workq.put(WorkMessage.ATT(value))
        elif event == Id.DIGPOW:
            value = values[event]
            window[Id.POWLBL].Update("Potenza: {} W".format(value))
            m.workq.put(WorkMessage.OUTPUT(value))
        elif event == Id.MAINTAB:
            if value := values[event]:
                m.tab = {
                    Id.TAB1: 1,
                    Id.TAB2: 2,
                    Id.TAB3: 3,
                    Id.TAB4: 4,
                    Id.TAB5: 5
                }[value]
                if value == Id.TAB4:
                    m.workq.put(WorkMessage.LOG())
        elif event == Id.DESTBTN:
            window[Id.DESTINATION].Update(values[event])
        elif event == Id.TEMPBTN:
            window[Id.TEMPLATE].Update(values[event])
        elif event in [Id.AUTOTEST, Id.RETRYAUTOTEST]:
            if event == Id.AUTOTEST:
                m.collectedData = None
            startAutomatedTest(m, window, values[Id.TEMPLATE],
                               values[Id.DESTINATION])

        if m.restart:
            m.restart = False
            startAutomatedTest(m, window, window[Id.TEMPLATE].Get(),
                               window[Id.DESTINATION].Get())

        try:
            msg: GuiMessage = guiq.get(timeout=0.1)

            def connected_rfg(m: SimpleNamespace):
                m.connected = True
                window[Id.CONNECT_STATUS1].Update("RFG2450 - Connesso!")
                window[Id.STATUS].Update("Connesso!")
                window[Id.TAB1].Update(disabled=False)
                window[Id.TAB1].Select()
                m.workq.put(WorkMessage.HANDSHAKE())

            def connected_arduino(m: SimpleNamespace):
                window[Id.CONNECT_STATUS2].Update("Arduino - Connesso!")
                m.connected_arduino = True

            def disconnected_arduino(m: SimpleNamespace):
                window[Id.CONNECT_STATUS2].Update("Arduino - Disconnesso!")
                m.connected_arduino = False

            def disconnected_rfg(m: SimpleNamespace):
                m.connected = False
                window[Id.STATUS].Update("Disconnesso!")
                window[Id.CONNECT_STATUS1].Update("RFG2450 - Disconnesso!")
                updateWidgets(m, window, config, config_arduino)
                sg.Popup("La connessione e' stata inaspettatamente interrotta",
                         title="Attenzione")

            def setMode(m: SimpleNamespace, x):
                m.mode = x
                selectMode(window, x),

            def reconnected(m: SimpleNamespace, window, template, destination):
                connected_rfg(m)
                m.restart = m.data_acquisition

            msg.match(
                connected_rfg=lambda: connected_rfg(m),
                connected_arduino=lambda: connected_arduino(m),
                disconnected_rfg=lambda: disconnected_rfg(m),
                disconnected_arduino=lambda: disconnected_arduino(m),
                send=lambda s: window[Id.LOG].update(
                    explicit(s), text_color_for_value="blue", append=True),
                recv=lambda s: window[Id.LOG].update(
                    explicit(s), text_color_for_value="black", append=True),
                serial=lambda x: window[Id.SN].Update(x),
                revision=lambda y: window[Id.REVISION].Update(
                    y.replace('\n', '\t')),
                power=lambda x, y, z:
                (window[Id.DIRPWR].Update("Potenza diretta: {} W".format(x)),
                 window[Id.REFPWR].Update("Potenza riflessa: {} W".format(
                     y)), window[Id.TEMP].Update("Temperatura: {}".format(
                         z)), window[Id.SWR].Update("VSWR: {}".format(
                             calculateVSWR(float(y), float(x))))),
                error=lambda: window[Id.STATUS].Update(
                    "Errore di comunicazione!"),
                error_arduino=lambda: window[Id.CONNECT_STATUS2].Update(
                    "Errore di comunicazione!"),
                attenuation=lambda x:
                (window[Id.ATT].Update("Attenuazione: {}".format(x), window[
                    Id.DIGATT].Update(value=x * 100)), window[Id.ATTLBL].
                 Update("Attenuazione: {}".format(x))),
                output=lambda x: window[Id.POW].Update("Potenza: {} W".format(
                    x)),
                log=lambda x, y, z: (window[Id.SN].Update(x), window[
                    Id.LOGHOURS].Update("Ore di lavoro: {}".format(y), window[
                        Id.LOGLOG].update(z))),
                mode=lambda x: setMode(m, x),
                reconnected=lambda: reconnected(m, window, window[
                    Id.TEMPLATE].Get(), window[Id.DESTINATION].Get()))

        except queue.Empty:
            pass

        if m.connected:
            if time.time() > m.timestamp + 2:
                if m.tab == 1:
                    m.workq.put(WorkMessage.GETPOWER())

                if m.mode == 1:
                    m.workq.put(WorkMessage.GETATT())
                elif m.mode == 3:
                    m.workq.put(WorkMessage.GETOUTPUT())

                m.timestamp = time.time()

    window.close()
