import PySimpleGUI as sg
from typing import List

from .elements import Id


def tab(width: int) -> List[List[sg.Element]]:
    return [
        [sg.Text("Ore di lavoro:", size=(40, 1), key=Id.LOGHOURS)],
        [sg.Multiline(size=(width, 24), disabled=True, key=Id.LOGLOG)],
    ]
