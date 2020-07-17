import PySimpleGUI as sg  # type: ignore
from queue import Queue, Empty
import parse
import time
from openpyxl import Workbook, load_workbook
import os
import datetime
from types import SimpleNamespace

from .elements import Id
from ..popups import *
from ...model import WorkMessage, GuiMessage
from ...utils.excelabstraction import CustomExcelWorkbookBecauseWindowsSucks

TMARGIN = 50
ATTENUATION = 32


def saveData(wb, data1, data2, destination, serial, ver):
    cellId = lambda x, y: "{}{}".format(chr(y), x)

    wb['C3'] = serial
    wb['C4'] = datetime.date.today().strftime("%d/%m/%Y")
    wb['C5'] = datetime.datetime.now().strftime("%I:%M:%S %p")
    wb['C6'] = ver

    for i in range(2):
        d = [data1, data2][i]

        for t in [25, 45]:
            srow = [11, 47][i]
            if i == 1 and t == 45:
                scol = 72
            else:
                scol = {25: 66, 45: 70}[t]

            for k in d[t].keys():
                wb[cellId(srow, 65)] = k
                wb[cellId(srow, scol)] = d[t][k][0]
                wb[cellId(srow, scol + 1)] = d[t][k][1]
                wb[cellId(srow, scol + 2)] = d[t][k][2]
                srow += 1

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


def automatedTestProcedure(m, w, template, destination):
    def readParameters(t, m, w):
        while True:
            if res := sendCommand(WorkMessage.SEND("Read_PAR"), m, w):
                try:
                    _, _, temp = parse.parse("PAR,{},Wf,{},Wr,{},C\r\n", res)
                    temp = float(temp)
                except TypeError:
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
                    break
            else:
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

        if res := sendCommand(WorkMessage.SEND("Read_ADC"), m, w):
            try:
                adcc, adcf, adcr, adct, adcp = parse.parse(
                    "{:d},{:d},{:d},{:d},{:d}\r\n", res)
            except TypeError:
                return False
        else:
            w[Id.STATUS].Update("Errore di comunicazione!")
            return False

        return (adcc, adcf, adcr, adct)

    def firstTest(temperature, m, w, data):
        attenuation = ATTENUATION

        while attenuation >= 0:
            if temperature in data.keys(
            ) and attenuation in data[temperature].keys():
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
                if not temperature in data.keys():
                    data[temperature] = {}

                _, values = w.Read(timeout=0)
                k = float(values[Id.K])
                adjusted = .5 * ((readings[0] * k) / .5)
                adjusted = adjustPopup(adjusted)

                data[temperature][attenuation] = [
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

    def secondTest(temperature, m, w, data):
        attenuation = ATTENUATION
        first = True

        while attenuation >= 0:
            if temperature in data.keys(
            ) and attenuation in data[temperature].keys():
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

            delay = 0
            while True:
                time.sleep(delay)
                delay = 0.5

                if values := readParameters(temperature, m, w):
                    _, adcf, adcr, _ = values

                    if False and adcf == 0 and adcr == 0:
                        if sg.PopupOKCancel(
                                "Il dispositivo e' in protezione; riprovare?",
                                keep_on_top=True,
                                title="Attenzione!") == "OK":
                            continue
                        else:
                            return False

                    if not temperature in data.keys():
                        data[temperature] = {}

                    data[temperature][attenuation] = [
                        values[1], values[2], values[3]
                    ]
                    break
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

    wb = CustomExcelWorkbookBecauseWindowsSucks(template)

    if m.collectedData:
        data1, data2 = m.collectedData
    else:
        data1 = {}
        data2 = {}
        m.collectedData = (data1, data2)

    w[Id.STATUS].Update(
        "Procedura di acquisizione automatica dei dati in corso...")

    if not sendCommand(WorkMessage.SEND("Set_FRQ,2450000"), m, w):
        w[Id.STATUS].Update("Errore di comunicazione!")
        return True

    if sn := sendCommand(WorkMessage.SEND("Read_SN"), m, w):
        if res := parse.parse("S/N,{}\r\n", sn):
            serialNumber = res.fixed[0]
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

    if not firstTest(25, m, w, data1):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not secondTest(25, m, w, data2):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not firstTest(45, m, w, data1):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not secondTest(45, m, w, data2):
        w[Id.STATUS].Update("Procedura interrotta!")
        return True

    if not sendCommand(WorkMessage.SEND("Set_ATT,32.00"), m, w):
        sg.Popup(
            title="ATTENZIONE!",
            keep_on_top=True,
            custom_text=
            "NON STACCARE L'ANTENNA SE LA POTENZA EROGATA SUPERA I 5 WATT!")
        return True

    if res := yesNoPopup("Procedura terminata. Salvare i dati?"):
        template = "{}_{}.xlsx".format(
            os.path.basename(template).replace(".xlsx", ""), serialNumber)
        saveData(wb, data1, data2,
                 os.path.join(os.path.abspath(destination), template),
                 serialNumber, swVer)

    m.collectedData = None
    w[Id.STATUS].Update("Procedura terminata!")
    return False
