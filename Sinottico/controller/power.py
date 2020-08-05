import itertools
from typing import List, Tuple
from types import SimpleNamespace
import random
import threading
import multiprocessing
import queue
import math

from ..model import *


def combinazioni() -> List[Tuple[int, int, int, int]]:
    return [*itertools.product(range(5, 40, 5), range(20, 105, 5), range(5, 50, 5), range(100, 2550, 50))]


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


def reflex_combinations_task(pardiretta: Tuple[int, int, int, int], data: DatiPotenza, guiq: queue.Queue):
    cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=cores)

    parametri = combinazioni()
    res = pool.starmap(calcolo_errore_riflessa,
                       ((pardiretta, x, data,) for x in parametri))

    maxerr = 0
    for x in random.sample(res, 10):
        maxerr = max(maxerr, x.err)

    res = list(filter(lambda x: x.err <= maxerr, res))

    res.sort(key=lambda x: x.err)
    res = res[0:10]

    guiq.put(GuiMessage.REFLEX_COMBINATIONS_FOUND(res))


def direct_combinations_task(data: DatiPotenza, guiq: queue.Queue):
    cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=cores)

    parametri = combinazioni()

    res = pool.starmap(calcolo_errore_diretta, ((x, data,) for x in parametri))

    maxerr = 0
    for x in random.sample(res, 10):
        maxerr = max(maxerr, x.err)

    res = list(filter(lambda x: x.err <= maxerr, res))

    res.sort(key=lambda x: x.err)
    res = res[0:10]

    guiq.put(GuiMessage.DIRECT_COMBINATIONS_FOUND(res))


def launch_find_best_combinations_direct(data: DatiPotenza, guiq: queue.Queue):
    t = threading.Thread(target=direct_combinations_task, args=(data, guiq))
    t.daemon = True
    t.start()


def launch_find_best_combinations_reflex(pardiretta: Tuple[int, int, int, int], data: DatiPotenza, guiq: queue.Queue):
    t = threading.Thread(target=reflex_combinations_task,
                         args=(pardiretta, data, guiq))
    t.daemon = True
    t.start()
