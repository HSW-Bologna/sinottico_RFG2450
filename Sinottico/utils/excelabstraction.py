import sys
import datetime
import os

#import logging
#logging.basicConfig(filename='sinottico.log', level=logging.INFO)


class CustomExcelWorkbookBecauseWindowsSucks:
    def _openpyxl_init(self, filename):
        self.native = False
        from openpyxl import Workbook, load_workbook
        self.wb = load_workbook(filename)
        self.ws = self.wb.active

    def __init__(self, filename):
        import platform
        if platform.system() in ["Windows", "windows"]:
            try:
                import win32com.client
                import pywintypes
                try:
                    self.native = True
                    self.excel = win32com.client.Dispatch('Excel.Application')
                    self.wb = self.excel.Workbooks.Open(
                        os.path.join(os.getcwd(), filename))
                    self.ws = self.wb.Worksheets(1)
                    print("Caricato il modulo Excel Nativo")
                except pywintypes.com_error:
                    print("Excel non installato, procedo con openpyxl")
                    self._openpyxl_init(filename)
            except ModuleNotFoundError:
                print("win32com non installato, procedo con openpyxl")
                self._openpyxl_init(filename)
        else:
            print("Sistema operativo superiore, procedo con openpyxl")
            self._openpyxl_init(filename)

    def __setitem__(self, id, value):
        if self.native:
            self.ws.Range(id).Value = value
        else:
            self.ws[id] = value

    def __del__(self):
        if self.native:
            self.excel.quit()

    def save(self, filename):
        if self.native:
            self.wb.SaveAs(os.path.join(os.getcwd(), filename))
        else:
            self.wb.save(filename=filename)
