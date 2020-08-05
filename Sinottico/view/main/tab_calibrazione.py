import PySimpleGUI as sg
from typing import List
from types import SimpleNamespace
import re

from ...controller.power import *
from ...resources import resourcePath
from .elements import Id
from ...utils.excelabstraction import CustomExcelWorkbookBecauseWindowsSucks


def list_column(id1: Id, id2: Id, id3: Id, idpar: Tuple[Id, Id, Id, Id]):
    return sg.Column([
        [sg.Button("Elabora", key=id1),
            sg.Image(resourcePath("loading.gif"), key=id2)],
        [sg.Listbox(values=[], key=id3, size=(32, 5))],
        [sg.Input(size=(6, 1), key=x) for x in idpar]
    ])


def tab(**kwargs) -> List[List[sg.Element]]:
    return [
        [
            sg.Input("", size=(48, 1), key=Id.LOADDATA, enable_events=True),
            sg.FileBrowse("File",
                          file_types=(('Excel files', "*.xlsx"), ),
                          size=(16, 1))
        ],

        [
            sg.Input("", size=(48, 1), key=Id.DESTDATA, enable_events=True),
            sg.FolderBrowse("Destinazione", size=(16, 1)),
        ],
        [
            list_column(Id.ELABORA_DIRETTA, Id.STATUS_CALCOLO, Id.LIST_DIRETTA,
                        (Id.PAR_DIR_A, Id.PAR_DIR_B, Id.PAR_DIR_C, Id.PAR_DIR_D)),
            list_column(Id.ELABORA_RIFLESSA,
                        Id.STATUS_CALCOLO_RIFLESSA, Id.LIST_RIFLESSA,
                        (Id.PAR_RIF_A, Id.PAR_RIF_B, Id.PAR_RIF_C, Id.PAR_RIF_D))
        ]
    ]


def direct_calculation_end(res: List[SimpleNamespace], m: SimpleNamespace, w: sg.Window):
    w[Id.LIST_DIRETTA].Update(
        values=["{},{},{},{}".format(x.a, x.b, x.c, x.d) for x in res]),
    m.calculating = False
    w[Id.STATUS_CALCOLO].Update(visible=False)


def reflex_calculation_end(res: List[SimpleNamespace], m: SimpleNamespace, w: sg.Window):
    w[Id.LIST_RIFLESSA].Update(
        values=["{},{},{},{}".format(x.a, x.b, x.c, x.d) for x in res]),
    m.calculating = False


def manage(m: SimpleNamespace, event: Id, value: str, w: sg.Window) -> bool:
    w[Id.ELABORA_DIRETTA].Update(
        disabled=(len(w[Id.LOADDATA].Get()) == 0) or m.calculating)
    w[Id.ELABORA_RIFLESSA].Update(
        disabled=(len(w[Id.LIST_DIRETTA].get()) == 0) or m.calculating)

    if m.calculating:
        w[Id.STATUS_CALCOLO].Update(visible=True)
        w[Id.STATUS_CALCOLO].UpdateAnimation(
            resourcePath("loading.gif"))
        w[Id.STATUS_CALCOLO_RIFLESSA].Update(visible=True)
        w[Id.STATUS_CALCOLO_RIFLESSA].UpdateAnimation(
            resourcePath("loading.gif"))
    else:
        w[Id.STATUS_CALCOLO].Update(visible=False)
        w[Id.STATUS_CALCOLO_RIFLESSA].Update(visible=False)

    for x in [Id.PAR_DIR_A, Id.PAR_DIR_B, Id.PAR_DIR_C, Id.PAR_DIR_D, Id.PAR_RIF_A, Id.PAR_RIF_B, Id.PAR_RIF_C, Id.PAR_RIF_D]:
        raw = w[x].get()
        new = re.sub("[^0-9]", "", raw)
        if raw != new:
            w[x].Update(new)

    if event == Id.ELABORA_DIRETTA:
        m.workbook = CustomExcelWorkbookBecauseWindowsSucks(
            w[Id.LOADDATA].Get())
        loaded_data = m.workbook.read_data()
        m.calculating = True
        m.workq.put(WorkMessage.FIND_DIRECT_COMBINATIONS(loaded_data))
    if event == Id.ELABORA_RIFLESSA:
        loaded_data = m.workbook.read_data()
        m.calculating = True
        p = [int(x) for x in w[Id.LIST_DIRETTA].get()[0].split(",")]
        pardiretta: Tuple[int, int, int, int] = (p[0], p[1], p[2], p[3])
        m.workq.put(WorkMessage.FIND_REFLEX_COMBINATIONS(
            pardiretta, loaded_data))
    else:
        return False
    return True
