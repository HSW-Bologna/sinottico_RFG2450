import sys
import datetime
import os


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
                except pywintypes.com_error:
                    self._openpyxl_init(filename)
            except ModuleNotFoundError:
                    self._openpyxl_init(filename)
        else:
            self._openpyxl_init(filename)
        print(self.native)

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
