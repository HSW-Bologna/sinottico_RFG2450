import PySimpleGUI as sg
import math
from typing import List, Tuple, Any

from .elements import Id

MODES = {"Modalita' {}".format(v): v for v in range(4)}


def needle(value: int, end: int = 300, blind_angle: int = 30, radius: int = 1) -> Tuple[int, int]:
    def radians(degrees: float):
        return degrees * (math.pi/180)
    active_angle = 360 - blind_angle
    value_angle = (value*active_angle)/end
    tmp = radians(270 - (blind_angle/2 + value_angle))
    return (int(math.cos(tmp) * radius), int(math.sin(tmp) * radius))


def update_gauge_dir(previous : Any, window: sg.Window, value: int):
    if previous:
        window[Id.GAUGE_DIR].delete_figure(previous)
    return window[Id.GAUGE_DIR].draw_line((0, 0), needle(
        value, radius=70, blind_angle=88), width=3)


def update_gauge_rif(previous : Any, window: sg.Window, value: int):
    if previous:
        window[Id.GAUGE_RIF].delete_figure(previous)
    return window[Id.GAUGE_RIF].draw_line((0, 0), needle(
        value, radius=70, blind_angle=88), width=3)


def calculateVSWR(pref, pfwr):
    import math
    if pfwr == 0:
        return None
    elif 1 - math.sqrt(pref / pfwr) == 0:
        return None
    else:
        return (1 + math.sqrt(pref / pfwr)) / (1 - math.sqrt(pref / pfwr))


def update_info(model : Any, window: sg.Window, x: int, y: int, z: str):
    window[Id.DIRPWR].Update("Potenza diretta: {} W".format(x))
    model.needle1 = update_gauge_dir(model.needle1, window, x)
    window[Id.REFPWR].Update("Potenza riflessa: {} W".format(y))
    model.needle2 = update_gauge_rif(model.needle2, window, y)
    window[Id.TEMP].Update("Temperatura: {}".format(z))
    window[Id.SWR].Update("VSWR: {}".format(calculateVSWR(float(y), float(x))))


def tab(width: int) -> List[List[sg.Element]]:
    sizew = width*8 #10

    return [
        [
            sg.Frame("Informazioni",
                     [[sg.Sizer(sizew, 0)],
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
                        sg.Tab("", [[sg.Sizer(sizew - 16, 0)],
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
                            sg.Text("Potenza: ", key=Id.POW, size=(32, 1)),
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
                [
                    sg.Column([
                        [
                            sg.Graph(canvas_size=(162, 162), graph_bottom_left=(-82,
                                                                                -82), graph_top_right=(82, 82), key=Id.GAUGE_DIR),
                        ],
                        [
                            sg.Text("Potenza diretta:",
                                    key=Id.DIRPWR, size=(24, 1)),
                        ]
                    ]),
                    sg.Column([
                        [
                            sg.Graph(canvas_size=(162, 162), graph_bottom_left=(-82,
                                                                                -82), graph_top_right=(82, 82), key=Id.GAUGE_RIF),
                        ],
                        [
                            sg.Text("Potenza riflessa:",
                                    key=Id.REFPWR, size=(24, 1))
                        ]
                    ]),
                    sg.Column([
                        [sg.Text("Temperatura: ", size=(24, 1), key=Id.TEMP)],
                        [sg.Text("VSWR: ", size=(12, 1), key=Id.SWR), ]
                    ])
                ],
            ],
                pad=(0, 20))
        ],
    ]
