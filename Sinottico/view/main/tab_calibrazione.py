import PySimpleGUI as sg
from typing import List
from types import SimpleNamespace
import re

from ...controller.power import *
from ...resources import resourcePath
from .elements import Id
from ...utils.excelabstraction import CustomExcelWorkbookBecauseWindowsSucks


def get_parameters(w: sg.Window, id1: Id, id2: Id, id3: Id, id4: Id) -> Tuple[int, int, int, int]:
    raw = []
    for el in [id1, id2, id3, id4]:
        if content := w[el].get():
            try:
                raw.append(int(content))
            except ValueError:
                raw.append(0)
        else:
            raw.append(0)
    return (raw[0], raw[1], raw[2], raw[3])


def set_parameters(w: sg.Window, id1: Id, id2: Id, id3: Id, id4: Id, pars: Tuple[int, int, int, int]) -> None:
    w[id1].update(pars[0])
    w[id2].update(pars[1])
    w[id3].update(pars[2])
    w[id4].update(pars[3])


def list_column(id1: Id, id2: Id, id3: Id, idpar: Tuple[Id, Id, Id, Id]):
    return sg.Column([
        [sg.Button("Elabora", key=id1),
            sg.Image(resourcePath("loading.gif"), key=id2)],
        [sg.Listbox(values=[], key=id3, size=(32, 5),
                    enable_events=True, bind_return_key=True)],
        [sg.Input(size=(6, 1), key=x, enable_events=True) for x in idpar]
    ])


def tab(**kwargs) -> List[List[sg.Element]]:
    return [
        [
            sg.Input("", disabled=True, size=(48, 1),
                     key=Id.LOADDATA, enable_events=True),
            sg.FileBrowse("File",
                          file_types=(('Excel files', "*.xlsx"), ),
                          size=(16, 1))
        ],

        [
            sg.Input("", disabled=True, size=(48, 1),
                     key=Id.DESTDATA, enable_events=True),
            sg.FolderBrowse("Destinazione", size=(16, 1)),
        ],
        [
            list_column(Id.ELABORA_DIRETTA, Id.STATUS_CALCOLO, Id.LIST_DIRETTA,
                        (Id.PAR_DIR_A, Id.PAR_DIR_B, Id.PAR_DIR_C, Id.PAR_DIR_D)),
            list_column(Id.ELABORA_RIFLESSA,
                        Id.STATUS_CALCOLO_RIFLESSA, Id.LIST_RIFLESSA,
                        (Id.PAR_RIF_A, Id.PAR_RIF_B, Id.PAR_RIF_C, Id.PAR_RIF_D))
        ],
        [
            sg.Button("Salva", key=Id.SAVE_PARAMETERS),
            sg.Button("Invia", key=Id.SEND_PARAMETERS)
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

    disabled = False
    for el in [Id.PAR_DIR_A, Id.PAR_DIR_B, Id.PAR_DIR_C, Id.PAR_DIR_D, Id.PAR_RIF_A, Id.PAR_RIF_B, Id.PAR_RIF_C, Id.PAR_RIF_D]:
        try:
            int(w[el].get())
        except ValueError:
            disabled = True
            break
    w[Id.SAVE_PARAMETERS].Update(disabled=(len(w[Id.DESTDATA].get()) == 0) or disabled)
    w[Id.SEND_PARAMETERS].update(disabled=disabled)

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

    if event == Id.LIST_DIRETTA:
        raw = [int(x) for x in w[Id.LIST_DIRETTA].get()[0].split(",")]
        pars = (raw[0], raw[1], raw[2], raw[3])
        set_parameters(w, Id.PAR_DIR_A, Id.PAR_DIR_B,
                       Id.PAR_DIR_C, Id.PAR_DIR_D, pars)
    elif event == Id.LIST_RIFLESSA:
        raw = [int(x) for x in w[Id.LIST_RIFLESSA].get()[0].split(",")]
        pars = (raw[0], raw[1], raw[2], raw[3])
        set_parameters(w, Id.PAR_RIF_A, Id.PAR_RIF_B,
                       Id.PAR_RIF_C, Id.PAR_RIF_D, pars)
    elif event == Id.ELABORA_DIRETTA:
        m.calculating = True
        m.workq.put(WorkMessage.FIND_DIRECT_COMBINATIONS(w[Id.LOADDATA].get()))
    elif event == Id.ELABORA_RIFLESSA:
        m.calculating = True
        pardiretta = get_parameters(
            w, Id.PAR_DIR_A, Id.PAR_DIR_B, Id.PAR_DIR_C, Id.PAR_DIR_D)
        m.workq.put(WorkMessage.FIND_REFLEX_COMBINATIONS(
            pardiretta, w[Id.LOADDATA].get()))
    elif event == Id.SAVE_PARAMETERS:
        filename = w[Id.LOADDATA].get()
        destination = os.path.join(
            w[Id.DESTDATA].get(), os.path.basename(filename))
        m.workq.put(WorkMessage.SAVE_PARAMETERS(filename, destination, get_parameters(
            w, Id.PAR_DIR_A, Id.PAR_DIR_B, Id.PAR_DIR_C, Id.PAR_DIR_D), get_parameters(w, Id.PAR_RIF_A, Id.PAR_RIF_B, Id.PAR_RIF_C, Id.PAR_RIF_D)))
    elif event == Id.SEND_PARAMETERS:
        m.workq.put(WorkMessage.SEND_PARAMETERS(get_parameters(w, Id.PAR_DIR_A, Id.PAR_DIR_B, Id.PAR_DIR_C, Id.PAR_DIR_D), 
            get_parameters(w, Id.PAR_RIF_A, Id.PAR_RIF_B, Id.PAR_RIF_C, Id.PAR_RIF_D)))
    else:
        return False
    return True
