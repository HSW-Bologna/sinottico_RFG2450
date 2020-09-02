import PySimpleGUI as sg
from typing import List

from ...resources import resourcePath
from .elements import Id


def tab(width: int) -> List[List[sg.Element]]:
    return [[
        sg.Multiline(size=(width, 25), key=Id.LOG,
                     autoscroll=True, disabled=True)
    ],
        [
        sg.Input(size=(width-4, None), key=Id.INPUT),
        sg.Button(image_filename=resourcePath('send.png'),
                  bind_return_key=True,
                  key=Id.SEND)
    ]]
