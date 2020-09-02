import PySimpleGUI as sg
from typing import List

from .elements import Id


def tab(width: int) -> List[List[sg.Element]]:
    return [
        [
            sg.Input("", disabled=True, size=(width - 18, 1), key=Id.TEMPLATE),
            sg.FileBrowse("Template",
                          file_types=(('Excel files', "*.xlsx"), ),
                          size=(16, 1),
                          key=Id.TEMPBTN),
        ],
        [
            sg.Input("", disabled=True, size=(width - 18, 1), key=Id.DESTINATION),
            sg.FolderBrowse("Destinazione", size=(16, 1), key=Id.DESTBTN),
        ],
        [
            sg.Spin(["{:.2f}".format(x / 100.) for x in range(5, 155, 5)],
                    initial_value="1.00",
                    change_submits=True,
                    size=(5, 1),
                    key=Id.K),
            sg.Text("Coefficiente K", size=(16, 1)),
        ],
        [
            sg.Spin([x for x in range(1, 80)],
                    initial_value="23",
                    change_submits=True,
                    size=(5, 1),
                    key=Id.TEMP_LOW),
            sg.Text("Temperatura bassa", size=(25, 1)),
            sg.Spin([x for x in range(1, 80)],
                    initial_value="43",
                    change_submits=True,
                    size=(5, 1),
                    key=Id.TEMP_HIGH),
            sg.Text("Temperatura alta", size=(25, 1)),
        ],
        [
            sg.Button("Avvio Procedura", key=Id.AUTOTEST),
            sg.Button("Riprendi", key=Id.RETRYAUTOTEST)
        ],
        [
            sg.Multiline(disabled=True,
                         autoscroll=True,
                         key=Id.LOGAUTO,
                         size=(width, 20))
        ],
    ]
