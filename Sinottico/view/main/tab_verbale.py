import PySimpleGUI as sg

from .elements import Id

tab = [
        [sg.Text("Ore di lavoro:", size=(40, 1), key=Id.LOGHOURS)],
        [sg.Multiline(size=(68, 20), disabled=True, key=Id.LOGLOG)],
    ]