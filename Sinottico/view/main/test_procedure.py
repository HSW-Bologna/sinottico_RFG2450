import PySimpleGUI as sg  # type: ignore
from queue import Queue, Empty
import time
from openpyxl import Workbook, load_workbook
import os
import datetime
from types import SimpleNamespace
import re

from .elements import Id
from ..popups import *
from ...model import WorkMessage, GuiMessage, ArduinoMessage, DatiPotenza
from ...utils.excelabstraction import CustomExcelWorkbookBecauseWindowsSucks
from ...controller.commands import parsePar

TMARGIN = 50
ATTENUATION = 2


def saveData(wb, data, destination, serial, ver):
    wb['C3'] = serial
    wb['C4'] = datetime.date.today().strftime("%d/%m/%Y")
    wb['C5'] = datetime.datetime.now().strftime("%I:%M:%S %p")
    wb['C6'] = ver
    wb.write_data(data)
    wb.save(destination)


def sendCommand(msg, m: SimpleNamespace, w):
    m.workq.put(msg)

    while True:
        msg = m.guiq.get()

        # Caso speciale di disconnessione
        if msg == GuiMessage.DISCONNECTED_RFG():
            m.guiq.put(msg)
            return None

        try:
            res = msg.recv()
            w[Id.LOGAUTO].Update(res,
                                 text_color_for_value="black",
                                 append=True)
            w.Refresh()
            return res
        except AttributeError:
            pass

        try:
            res = msg.send()
            w[Id.LOGAUTO].Update(res, text_color_for_value="blue", append=True)
            w.Refresh()
        except AttributeError:
            pass

        try:
            res = msg.error()
            w.Refresh()
            return None
        except AttributeError:
            pass

        try:
            res = msg.disconnected()
            m.guiq.put(msg)
            w.Refresh()
            return None
        except AttributeError:
            pass


def automatedTestProcedure(m : SimpleNamespace,
                           w : sg.Window,
                           template : str,
                           destination : str,
                           temp_bassa : int=23,
                           temp_alta : int=43):

    def readParameters(t : int, m : SimpleNamespace, w : sg.Window):
        assert(t == 25 or t == 45)

        while True:
            if res := sendCommand(WorkMessage.SEND("Read_PAR"), m, w):
                if res := parsePar(res):
                    _, _, temp = res
                    temp = float(temp)
                else:
                    w[Id.STATUS].Update("Errore di comunicazione!")
                    return False

                if not (temp >= t - TMARGIN and temp <= t + TMARGIN):
                    if popupTimedCancel(
                            "Attenzione!",
                            "Mantenere il dispositivo alla temperatura di {:.2f} C!"
                            .format(t),
                            10,
                            key="Interrompi") == "Interrompi":
                        w[Id.STATUS].Update("Procedura interrotta")
                        return False
                    else:
                        m.ardq.put(
                            ArduinoMessage.TEMPERATURE({
                                25: temp_bassa,
                                45: temp_alta
                            }[t]))
                else:
                    break
            else:
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

        if res := sendCommand(WorkMessage.SEND("Read_ADC"), m, w):
            if res := re.match("{0},{0},{0},{0},{0}\r\n".format("(\d+)"), res):
                adcc, adcf, adcr, adct, adcp = res.groups()
            else:
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

        try:
            return tuple(map(int, (adcc, adcf, adcr, adct,)))
        except ValueError:  # Ho estratto i valori come puramente numerici da una regex, non dovrebbe succedere
            return False

    def firstTest(temperature : int, m : SimpleNamespace, w : sg.Window):
        assert(temperature == 25 or temperature == 45)
        attenuation = ATTENUATION

        m.ardq.put(
            ArduinoMessage.TEMPERATURE({
                25: temp_bassa,
                45: temp_alta
            }[temperature]))

        while attenuation >= 0:
            if attenuation in m.collected_data.diretta[temperature].keys():
                attenuation -= 1
                continue
            else:
                break

        # I dati sono gia' stati raccolti
        if attenuation < 0:
            return True

        if not sendCommand(
                WorkMessage.SEND("Set_ATT,{:.2f}".format(attenuation)), m, w):
            w[Id.STATUS].Update("Errore di comunicazione!")
            return False

        if not sg.Popup(
                "Verifica carico 500HM correttamente inserito e temperatura impostata {:.2f} C"
                .format(temperature),
                keep_on_top=True,
                title="Attenzione!"):
            w[Id.STATUS].Update("Procedura interrotta!")
            return False

        while attenuation >= 0:
            if readings := readParameters(temperature, m, w):
                _, values = w.Read(timeout=0)
                k = float(values[Id.K])
                adjusted = .5 * ((readings[0] * k) / .5)
                adjusted = adjustPopup(adjusted)

                m.collected_data.diretta[temperature][attenuation] = [
                    readings[1], readings[3], adjusted
                ]
            else:
                return False

            if attenuation <= 0:
                break

            attenuation -= 1
            if not sendCommand(
                    WorkMessage.SEND("Set_ATT,{:.2f}".format(attenuation)), m,
                    w):
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

        return True

    def secondTest(temperature : int, m : SimpleNamespace, w : sg.Window):
        assert(temperature == 25 or temperature == 45)
        attenuation = ATTENUATION
        first = True

        m.ardq.put(
            ArduinoMessage.TEMPERATURE({
                25: temp_bassa,
                45: temp_alta
            }[temperature]))

        while attenuation >= 0:
            if attenuation in m.collected_data.riflessa[temperature].keys():
                attenuation -= 1
                continue
            else:
                break

        # I dati sono gia' stati raccolti
        if attenuation < 0:
            return True

        if not sendCommand(WorkMessage.SEND("Set_ATT,{:.2f}".format(attenuation)), m, w):
            w[Id.STATUS].Update("Errore di comunicazione!")
            return False

        if not sg.Popup(
                "Inserire correttamente tappo in corto e temperatura impostata a {:.2f} C"
                .format(temperature),
                keep_on_top=True,
                title="Attenzione!"):
            w[Id.STATUS].Update("Procedura interrotta!")
            return False

        while attenuation >= 0:
            if not first:
                delayPopup(0.5)
            else:
                first = False

            delay : float = 0
            while True:
                time.sleep(delay)
                delay = 0.5

                if values := readParameters(temperature, m, w):
                    _, adcf, adcr, _ = values

                    if adcf == 0 and adcr == 0 and False:
                        if sg.PopupOKCancel(
                                "Il dispositivo e' in protezione; riprovare?",
                                keep_on_top=True,
                                title="Attenzione!") == "OK":
                            if not sendCommand(WorkMessage.SEND("Set_ATT,{:.2f}".format(attenuation)), m, w):
                                w[Id.STATUS].Update("Errore di comunicazione!")
                                return False
                            continue
                        else:
                            return False

                    m.collected_data.riflessa[temperature][attenuation] = (
                        values[1], values[2], values[3]
                    )
                    break
                else:
                    return False

            if attenuation <= 0:
                break

            attenuation -= 1
            if not sendCommand(WorkMessage.SEND("Set_ATT,{:.2f}".format(attenuation)), m, w):
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

        return True

    wb = CustomExcelWorkbookBecauseWindowsSucks(template)

    w[Id.STATUS].Update(
        "Procedura di acquisizione automatica dei dati in corso...")

    if not sendCommand(WorkMessage.SEND("Set_FRQ,2450000"), m, w):
        w[Id.STATUS].Update("Errore di comunicazione!")
        return True

    if sn := sendCommand(WorkMessage.SEND("Read_SN"), m, w):
        if res := re.match("S/N,(\d+)\r\n", sn):
            serialNumber = res.groups()[0]
        else:
            w[Id.STATUS].Update("Errore di comunicazione!")
            return True
    else:
        w[Id.STATUS].Update("Errore di comunicazione!")
        return True

    if sw := sendCommand(WorkMessage.SEND("Read_REV"), m, w):
        swVer = sw.split('\r\n')[1].replace("FW Ver. ", '')
    else:
        w[Id.STATUS].Update("Errore di comunicazione!")
        return True

    if not sendCommand(WorkMessage.SEND("Set_MODE,0"), m, w):
        w[Id.STATUS].Update("Errore di comunicazione!")
        return True

    if not firstTest(25, m, w):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not secondTest(25, m, w):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not firstTest(45, m, w):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not secondTest(45, m, w):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not sendCommand(WorkMessage.SEND("Set_ATT,32.00"), m, w):
        sg.Popup(
            title="ATTENZIONE!",
            keep_on_top=True,
            custom_text="NON STACCARE L'ANTENNA SE LA POTENZA EROGATA SUPERA I 5 WATT!")
        return True

    if res := yesNoPopup("Procedura terminata. Salvare i dati?"):
        template = "{}_{}.xlsx".format(
            os.path.basename(template).replace(".xlsx", ""), serialNumber)
        saveData(wb, m.collected_data,
                 os.path.join(os.path.abspath(destination), template),
                 serialNumber, swVer)

    m.collected_data = DatiPotenza()
    w[Id.STATUS].Update("Procedura terminata!")
    return False
