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

        if self.excel:
            self.excel.quit()

    def _open_excel(self, filename):
        try:
            import win32com.client
            import pywintypes
            try:
                self.native = True
                self.excel = win32com.client.Dispatch('Excel.Application')
                self.wb = self.excel.Workbooks.Open(filename)
                self.ws = self.wb.Worksheets(1)
                #print("Caricato il modulo Excel Nativo")
            except pywintypes.com_error as e:
                #print("Excel non installato, procedo con openpyxl")
                return False
        except ModuleNotFoundError:
            #print("win32com non installato, procedo con openpyxl")
            return False
        return True

    def __init__(self, filename):
        self.excel = None
        filename = os.path.abspath(filename)
        # print(filename)
        import platform
        if platform.system() in ["Windows", "windows"]:
            if not self._open_excel(filename):
                if self.excel != None:
                    self.excel.quit()
                    if self._open_excel(filename):
                        return
                self._openpyxl_init(filename)
        else:
            #print("Sistema operativo superiore, procedo con openpyxl")
            self._openpyxl_init(filename)

    def __setitem__(self, id, value):
        if self.native:
            self.ws.Range(id).Value = value
        else:
            self.ws[id] = value

    def __del__(self):
        if self.native and self.excel:
            self.excel.quit()

    def save(self, filename):
        if self.native:
            self.wb.SaveAs(os.path.abspath(filename))
        else:
            self.wb.save(filename=filename)
