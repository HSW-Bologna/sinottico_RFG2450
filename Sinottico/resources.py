import sys
import os

def resourcePath(relative):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'assets'))

    return os.path.join(base_path, relative)

