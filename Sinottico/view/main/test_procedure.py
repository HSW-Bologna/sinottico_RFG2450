import PySimpleGUI as sg  # type: ignore
from queue import Queue, Empty
import parse
import time
from openpyxl import Workbook, load_workbook
import os
import datetime

from .elements import Id
from ..delayPopup import delayPopup
from ..yesNoPopup import yesNoPopup
from ..adjustPopup import adjustPopup
from ...model import WorkMessage
from ...controller.commands import parseSerialNumber, parsePar

TMARGIN = 50


def saveData(wb, data1, data2, destination, serial, ver):
    cellId = lambda x, y: "{}{}".format(chr(y), x)
    ws = wb.active

    ws['C3'] = serial
    ws['C4'] = datetime.date.today().strftime("%d/%m/%Y")
    ws['C5'] = datetime.datetime.now().strftime("%I:%M:%S %p")
    ws['C6'] = ver

    for i in range(2):
        d = [data1, data2][i]

        for t in [25, 45]:
            srow = [11, 47][i]
            if i == 1 and t == 45:
                scol = 72
            else:
                scol = {25: 66, 45: 70}[t]

            for k in d[t].keys():
                ws[cellId(srow, 65)] = k
                ws[cellId(srow, scol)] = d[t][k][0]
                ws[cellId(srow, scol + 1)] = d[t][k][1]
                ws[cellId(srow, scol + 2)] = d[t][k][2]
                srow += 1

    wb.save(filename=destination)


def sendCommand(msg, w, workq, guiq):
    workq.put(msg)

    while True:
        msg = guiq.get()
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
            guiq.put(msg)
            w.Refresh()
            return None
        except AttributeError:
            pass


def automatedTestProcedure(w, workq, guiq, template, destination):
    def readParameters(t, w, workq, guiq):
        while True:
            if res := sendCommand(WorkMessage.SEND("Read_PAR"), w, workq,
                                  guiq):
                _, _, temp = parse.parse("PAR,{},Wf,{},Wr,{},C\r\n", res)
                temp = float(temp)

                if not (temp >= t - TMARGIN and temp <= t + TMARGIN):
                    if not sg.PopupTimed(
                            "Mantenere il dispositivo alla temperatura di {:.2f} C!"
                            .format(t),
                            title="Attenzione!",
                            keep_on_top=True,
                            auto_close_duration=10):
                        w[Id.STATUS].Update("Procedura interrotta!")
                        return False
                else:
                    break
            else:
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

        if res := sendCommand(WorkMessage.SEND("Read_ADC"), w, workq, guiq):
            adcc, adcf, adcr, adct, adcp = parse.parse(
                "{:d},{:d},{:d},{:d},{:d}\r\n", res)
        else:
            w[Id.STATUS].Update("Errore di comunicazione!")
            return False

        return (adcc, adcf, adcr, adct)

    def firstTest(temperature, w, workq, guiq, data):
        attenuation = 32

        while attenuation >= 0:
            if not sendCommand(
                    WorkMessage.SEND("Set_ATT,{:.2f}".format(attenuation)), w,
                    workq, guiq):
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

            if not sg.Popup(
                    "Verifica carico 500HM correttamente inserito e temperatura impostata {:.2f} C"
                    .format(temperature),
                    keep_on_top=True,
                    title="Attenzione!"):
                w[Id.STATUS].Update("Procedura interrotta!")
                return False

            if readings := readParameters(temperature, w, workq, guiq):
                if not temperature in data.keys():
                    data[temperature] = {}

                _, values = w.Read(timeout=0)
                k = float(values[Id.K])
                adjusted = adjustPopup(readings[0] * k)

                data[temperature][attenuation] = [
                    readings[1], readings[3], adjusted
                ]
            else:
                return False

            attenuation -= 1

        return True

    def secondTest(temperature, w, workq, guiq, data):
        attenuation = 32

        while attenuation >= 0:
            if not sendCommand(
                    WorkMessage.SEND("Set_ATT,{:.2f}".format(attenuation)), w,
                    workq, guiq):
                w[Id.STATUS].Update("Errore di comunicazione!")
                return False

            if attenuation != 32:
                delayPopup(10)

            if not sg.Popup(
                    "Inserire correttamente tappo in corto e temperatura impostata a {:.2f} C"
                    .format(temperature),
                    keep_on_top=True,
                    title="Attenzione!"):
                w[Id.STATUS].Update("Procedura interrotta!")
                return False

            if values := readParameters(temperature, w, workq, guiq):
                if not temperature in data.keys():
                    data[temperature] = {}

                data[temperature][attenuation] = [
                    values[1], values[2], values[3]
                ]
            else:
                return False

            attenuation -= 1

        return True

    wb = load_workbook(template)
    ws = wb.active
    data1 = {}
    data2 = {}

    w[Id.STATUS].Update(
        "Procedura di acquisizione automatica dei dati in corso...")

    if not sendCommand(WorkMessage.SEND("Set_FRQ,2450000"), w, workq, guiq):
        return

    if sn := sendCommand(WorkMessage.SEND("Read_SN"), w, workq, guiq):
        serialNumber = parseSerialNumber(sn)
    else:
        return

    if sw := sendCommand(WorkMessage.SEND("Read_REV"), w, workq, guiq):
        swVer = sw.split('\r\n')[1].replace("FW Ver. ", '')
    else:
        return

    if not sendCommand(WorkMessage.SEND("Set_MODE,0"), w, workq, guiq):
        return

    if not firstTest(25, w, workq, guiq, data1):
        return

    if not secondTest(25, w, workq, guiq, data2):
        return

    if not firstTest(45, w, workq, guiq, data1):
        return

    if not secondTest(45, w, workq, guiq, data2):
        return

    if not sendCommand(WorkMessage.SEND("Set_ATT,32.00"), w, workq, guiq):
        sg.Popup(
            title="ATTENZIONE!",
            keep_on_top=True,
            custom_text=
            "NON STACCARE L'ANTENNA SE LA POTENZA EROGATA SUPERA I 5 WATT!")
        return

    if res := yesNoPopup("Procedura terminata. Salvare i dati?"):
        saveData(wb, data1, data2,
                 os.path.join(destination, os.path.basename(template)), serialNumber, swVer)

    w[Id.STATUS].Update("Procedura terminata!")