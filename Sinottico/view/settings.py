from enum import Enum
import PySimpleGUI as sg # type: ignore
from ..utils.serialutils import serialPorts
from ..model import *

class Id(Enum):
    OK = 2
    SERIALS = 4
    BRATES = 5
    DBITS = 6
    SBITS = 7
    PARITY = 8
    FCTRL = 9
    END = 12

def settingsWindow(config: SerialConfig):
    BAUDRATES = [4800, 9600, 19200, 38400, 57600, 115200, 230400]

    csize = (16, 1)
    ports = serialPorts()

    if config.port != None and config.port in ports:
        defport = config.port
    elif ports:
        defport = ports[0]
    else:
        defport = None


    layout = [
        [sg.Frame('Configurazione',
                  [
                      [sg.Column([[sg.Text('Porta')],
                                  [sg.Text('Baudrate')],
                                  [sg.Text('Data bits')],
                                  [sg.Text('Stop bits')],
                                  [sg.Text('Parity')],
                                  [sg.Text('Flow control')]]),

                       sg.Column([[sg.Combo(ports, key=Id.SERIALS, default_value=defport, size=csize)],
                                  [sg.Combo(BAUDRATES, key=Id.BRATES,
                                            default_value=config.baud, size=csize)],
                                  [sg.Combo([8, 9], key=Id.DBITS,
                                            default_value=config.data, size=csize)],
                                  [sg.Combo([0, 1, 2], key=Id.SBITS,
                                            default_value=config.stop, size=csize)],
                                  [sg.Combo(["None", "Even", "Odd"],
                                            key=Id.PARITY, default_value=config.parity, size=csize)],
                                  [sg.Combo(["None"], key=Id.FCTRL, default_value=config.flowctrl, size=csize)]])],
                      
                  ]),
            sg.Frame('Trasmissione',
                     [[sg.Text('Fine'), sg.Combo(['Niente', 'CR', 'LF', 'CR+LF'], default_value=config.end, key=Id.END)]]),
         ],
        [sg.Button('Ok', key=Id.OK)]]
    window = sg.Window('Impostazioni', layout, finalize=True, keep_on_top=True)

    while True:
        event, values = window.read()
        if event in (None,):   # if user closes window or clicks cancel
            return config

        if event == Id.OK:
            window.close()
            return SerialConfig(port=values[Id.SERIALS], baud=values[Id.BRATES],
                                data=values[Id.DBITS], stop=values[Id.SBITS],
                                parity=values[Id.PARITY], flowctrl=values[Id.FCTRL], end=values[Id.END])
        else:
            print(event, values)

