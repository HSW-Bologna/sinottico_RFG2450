import PySimpleGUI as sg
from typing import List

from .elements import Id

tab: List[List[sg.Element]] = [
    [
        sg.Input("", size=(48, 1), key=Id.LOADDATA),
        sg.FileBrowse("File",
                      file_types=(('Excel files', "*.xlsx"), ),
                      size=(16, 1),
                      key=Id.LOADDATABTN),
    ]
]
