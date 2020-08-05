import PySimpleGUI as sg

from ...resources import resourcePath
from .elements import Id

tab = [[
    sg.Multiline(size=(64, 20), key=Id.LOG, autoscroll=True, disabled=True)
],
    [
    sg.Input(size=(60, None), key=Id.INPUT),
    sg.Button(image_filename=resourcePath('send.png'),
              bind_return_key=True,
              key=Id.SEND)
]]
