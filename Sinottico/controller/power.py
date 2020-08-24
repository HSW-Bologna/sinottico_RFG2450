import itertools
from typing import List, Tuple
from types import SimpleNamespace
import random
import threading
import multiprocessing
import queue
import math

from ..model import *
from ..utils.excelabstraction import *


def combinazioni_diretta() -> List[Tuple[int, int, int, int]]:
    return [*itertools.product(range(10, 35, 5), range(50, 310, 10), range(0, 28, 2), range(1000, 5000, 100))]


def combinazioni_riflessa() -> List[Tuple[int, int, int, int]]:
    return [*itertools.product(range(4, 22, 2), range(50, 350, 10), range(4, 20, 2), range(500, 3500, 50))]


def calcolo_potenza(adcf: int, adct: int, a: int, b: int, c: int, d: int) -> float:
    if (res := ((a*adcf*adcf)/100000)-(((d-adct)*adcf*b)/10000000)-c) < 0:
        return 0
    else:
        return res


def stima_potenza_riflessa(att: float, diretta: float, a: int, b: int, c: int, d: int) -> float:
    try:
        sti = (10. ** ((10.*math.log(1000.*diretta) - att)/10.))/1000.
        return sti
    except ValueError:
        return 0


def calcolo_errore_diretta(parametri: Tuple[int, int, int, int], data: DatiPotenza):
    a, b, c, d = parametri
    err: float = 0
    result: List[SimpleNamespace] = []

    diretta25: List[Tuple[int, ...]] = [
        (k, *v) for k, v in data.diretta[25].items()]
    diretta45: List[Tuple[int, ...]] = [
        (k, *v) for k, v in data.diretta[45].items()]

    for diretta in [diretta25, diretta45]:
        for (att, adcf, adct, pfmes) in diretta:
            pfcal = calcolo_potenza(adcf, adct, a, b, c, d)
            err += abs(pfcal - pfmes)

    return SimpleNamespace(a=a, b=b, c=c, d=d, err=err)


def calcolo_errore_riflessa(pardiretta: Tuple[int, int, int, int], parametri: Tuple[int, int, int, int], data: DatiPotenza):
    a, b, c, d = parametri
    a0, b0, c0, d0 = pardiretta
    err: float = 0
    result: List[SimpleNamespace] = []

    diretta25: List[Tuple[int, ...]] = [
        (k, *v) for k, v in data.diretta[25].items()]
    diretta45: List[Tuple[int, ...]] = [
        (k, *v) for k, v in data.diretta[45].items()]

    for diretta in [diretta25, diretta45]:
        for (att, adcf, adct, pfmes) in diretta:
            pfcal = calcolo_potenza(adcf, adct, a0, b0, c0, d0)
            prsti = stima_potenza_riflessa(data.ciscolatore, pfcal, a, b, c, d)
            err += abs(pfcal - prsti)

    return SimpleNamespace(a=a, b=b, c=c, d=d, err=err)


def reflex_combinations_task(pardiretta: Tuple[int, int, int, int], sheet: str, guiq: queue.Queue):
    try:
        workbook = CustomExcelWorkbookBecauseWindowsSucks(sheet)
        data = workbook.read_data()
    except (FileNotFoundError, ValueError):
        guiq.put(GuiMessage.DIRECT_COMBINATIONS_FOUND([]))
        guiq.put(GuiMessage.ERROR("Documento di calcolo non valido!"))
        return

    cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=cores)

    parametri = combinazioni_riflessa()
    res = pool.starmap(calcolo_errore_riflessa,
                       ((pardiretta, x, data,) for x in parametri))

    maxerr = 0
    for x in random.sample(res, 10):
        maxerr = max(maxerr, x.err)

    res = list(filter(lambda x: x.err <= maxerr, res))

    res.sort(key=lambda x: x.err)
    res = res[0:10]

    guiq.put(GuiMessage.REFLEX_COMBINATIONS_FOUND(res))


def direct_combinations_task(sheet: str, guiq: queue.Queue):
    try:
        workbook = CustomExcelWorkbookBecauseWindowsSucks(sheet)
        data = workbook.read_data()
    except (FileNotFoundError, ValueError):
        guiq.put(GuiMessage.DIRECT_COMBINATIONS_FOUND([]))
        guiq.put(GuiMessage.ERROR("Documento di calcolo non valido!"))
        return

    cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=cores)

    parametri = combinazioni_diretta()

    res = pool.starmap(calcolo_errore_diretta, ((x, data,) for x in parametri))

    maxerr = 0
    for x in random.sample(res, 10):
        maxerr = max(maxerr, x.err)

    res = list(filter(lambda x: x.err <= maxerr, res))

    res.sort(key=lambda x: x.err)
    res = res[0:10]

    guiq.put(GuiMessage.DIRECT_COMBINATIONS_FOUND(res))


def launch_find_best_combinations_direct(sheet: str, guiq: queue.Queue):
    t = threading.Thread(target=direct_combinations_task, args=(sheet, guiq))
    t.daemon = True
    t.start()


def launch_find_best_combinations_reflex(pardiretta: Tuple[int, int, int, int], sheet: str, guiq: queue.Queue):
    t = threading.Thread(target=reflex_combinations_task,
                         args=(pardiretta, sheet, guiq))
    t.daemon = True
    t.start()


def save_parameters(sheet: str, dest: str, pardiretta: Tuple[int, int, int, int], parriflessa: Tuple[int, int, int, int], guiq: queue.Queue):
    try:
        workbook = CustomExcelWorkbookBecauseWindowsSucks(sheet)
        workbook.write_parametri(pardiretta, parriflessa)
        workbook.save(dest)
    except (FileNotFoundError, ValueError):
        guiq.put(GuiMessage.ERROR("Documento di calcolo non valido!"))
        return
