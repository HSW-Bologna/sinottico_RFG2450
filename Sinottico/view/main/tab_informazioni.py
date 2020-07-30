import PySimpleGUI as sg

from .elements import Id

MODES = {"Modalita' {}".format(v): v for v in range(4)}

tab = [
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

