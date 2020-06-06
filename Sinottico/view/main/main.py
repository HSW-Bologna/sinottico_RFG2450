from queue import Queue
import queue
from enum import Enum, auto
import PySimpleGUI as sg  # type: ignore
from ..settings import settingsWindow
from ...resources import resourcePath
from ...model import *
from .elements import Id
from .test_procedure import automatedTestProcedure

MODES = {"Modalita' {}".format(v): v for v in range(4)}


def explicit(s):
    return s.replace('\r', '\\r').replace('\n', '\\n\n')


def startAutomatedTest(w, workq, guiq, template, destination):
    elements = [
        Id.SETTINGS, Id.CONNECT, Id.TAB1, Id.TAB3, Id.TAB4, Id.TAB5,
        Id.AUTOTEST
    ]
    [w[x].Update(disabled=True) for x in elements]
    automatedTestProcedure(w, workq, guiq, template, destination)
    [w[x].Update(disabled=False) for x in elements]


def mainWindow(workq: Queue, guiq: Queue):
    sg.theme("DefaultNoMoreNagging")
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
            sg.TabGroup([[
                sg.Tab(
                    list(MODES.keys())[0], [[
                        sg.Text(
                            "Attenuazione: 0.00", size=(20, 1), key=Id.ATTLBL),
                        sg.Slider(range=(0, 3200),
                                  resolution=25,
                                  disable_number_display=True,
                                  tooltip="Attenuazione",
                                  orientation="horizontal",
                                  enable_events=True,
                                  key=Id.DIGATT)
                    ]]),
                sg.Tab(
                    list(MODES.keys())[1],
                    [[sg.Text("Attenuazione: ", key=Id.ATT, size=(32, 1))]]),
                sg.Tab(
                    list(MODES.keys())[2], [[
                        sg.Text("Potenza: 0 W", size=(20, 1), key=Id.POWLBL),
                        sg.Slider(range=(0, 300),
                                  orientation="horizontal",
                                  enable_events=True,
                                  disable_number_display=True,
                                  key=Id.DIGPOW)
                    ]]),
                sg.Tab(
                    list(MODES.keys())[3],
                    [[sg.Text("Potenza: ", key=Id.POW, size=(32, 1))]]),
            ]],
                        key=Id.MODES,
                        enable_events=True),
        ],
        [
            sg.Frame("Parametri", [
                [sg.Text("Potenza diretta:", key=Id.DIRPWR, size=(32, 1))],
                [sg.Text("Potenza riflessa:", key=Id.REFPWR, size=(32, 1))],
                [
                    sg.Text("Temperatura: ", size=(32, 1), key=Id.TEMP),
                    sg.Text("SWR: ", size=(32, 1)),
                ],
            ])
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
                    size=(5, 1),
                    key=Id.K),
            sg.Text("Coefficiente K")
        ],
        [sg.Button("Avvio Procedura", key=Id.AUTOTEST)],
        [
            sg.Multiline(disabled=True,
                         autoscroll=True,
                         key=Id.LOGAUTO,
                         size=(64, 15))
        ],
    ]

    tab3: List[List[sg.Element]] = [[]]

    tab4 = [
        [sg.Text("Ore di lavoro:", size=(40, 1), key=Id.LOGHOURS)],
        [sg.Multiline(size=(64, 20), disabled=True, key=Id.LOGLOG)],
    ]

    tab5 = [[
        sg.Multiline(size=(64, 20), key=Id.LOG, autoscroll=True, disabled=True)
    ],
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
                  sg.Text("Selezionare una porta e connetersi",
                          key=Id.STATUS,
                          size=(64, 1))
              ]]

    # Create the Window
    window = sg.Window('Window Title', layout, finalize=True)

    config = SerialConfig()

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        window[Id.CONNECT].Update(disabled=not config.port)
        [
            window[x].Update(disabled=not connected) for x in
            [Id.SEND, Id.INFO, Id.TAB1, Id.TAB2, Id.TAB3, Id.TAB4, Id.TAB5]
        ]

        event, values = window.read(timeout=0.1, timeout_key=Id.TIMEOUT)
        if event in (None, 'Cancel'):  # if user closes window or clicks cancel
            break

        window[Id.AUTOTEST].Update(
            disabled=not (values[Id.TEMPLATE] and values[Id.DESTINATION]))

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
        elif event == Id.SEND:
            workq.put(WorkMessage.SEND(values[Id.INPUT]))
        elif event == Id.INFO:
            workq.put(WorkMessage.GETINFO())
        elif event == Id.MODES:
            element, value = window[event], values[event]
            workq.put(WorkMessage.MODE(MODES[value]))
        elif event == Id.TIMEOUT:
            pass
        elif event == Id.DIGATT:
            value = values[event] / 100.
            window[Id.ATTLBL].Update("Attenuazione: {:.2f}".format(value))
            workq.put(WorkMessage.ATT(value))
        elif event == Id.DIGPOW:
            value = values[event]
            window[Id.POWLBL].Update("Potenza: {} W".format(value))
            workq.put(WorkMessage.OUTPUT(value))
        elif event == Id.MAINTAB:
            value = values[event]

            if value == Id.TAB1:
                workq.put(WorkMessage.SELECTEDTAB(1))
            elif value == Id.TAB4:
                workq.put(WorkMessage.LOG())
                workq.put(WorkMessage.SELECTEDTAB(4))
            elif value != None:
                workq.put(WorkMessage.SELECTEDTAB(0))
        elif event == Id.DESTBTN:
            window[Id.DESTINATION].Update(values[event])
        elif event == Id.TEMPBTN:
            window[Id.TEMPLATE].Update(values[event])
        elif event == Id.AUTOTEST:
            startAutomatedTest(window, workq, guiq, values[Id.TEMPLATE],
                               values[Id.DESTINATION])
        else:
            print(event)

        try:
            msg: GuiMessage = guiq.get(timeout=0.1)

            def connected():
                nonlocal connected
                connected = True
                window[Id.STATUS].Update("Connesso!")
                window[Id.TAB1].Update(disabled=False)
                window[Id.TAB1].Select()

            def disconnected():
                nonlocal connected
                connected = False
                window[Id.STATUS].Update("Disconnesso!")

            msg.match(
                connected=connected,
                disconnected=disconnected,
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
                     y)), window[Id.TEMP].Update("Temperatura: {}".format(z))),
                error=lambda: window[Id.STATUS].Update(
                    "Errore di comunicazione!"),
                attenuation=lambda x: window[Id.ATT].Update("Attenuazione: {}".
                                                            format(x)),
                output=lambda x: window[Id.POW].Update("Potenza: {} W".format(
                    x)),
                log=lambda x, y, z: (window[Id.SN].Update(x), window[
                    Id.LOGHOURS].Update("Ore di lavoro: {}".format(y), window[
                        Id.LOGLOG].update(z))))

        except queue.Empty:
            pass

    window.close()
