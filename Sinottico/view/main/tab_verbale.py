import PySimpleGUI as sg

from .elements import Id


def tab(**kwargs):
    return [
        [sg.Text("Ore di lavoro:", size=(64, 1), key=Id.LOGHOURS)],
        [sg.Multiline(size=(64, 20), disabled=True, key=Id.LOGLOG)],
    ]
