from queue import Queue
import threading
import PySimpleGUI as sg  # type: ignore

from .view.main import mainWindow
from .controller import controllerTask

def main():
    workq: queue.Queue = Queue()
    guiq: queue.Queue = Queue()

    t = threading.Thread(target=controllerTask, args=(guiq, workq))
    t.daemon = True
    t.start()

    sg.theme("DefaultNoMoreNagging")
    mainWindow(workq, guiq)

if __name__ == '__main__':
    main()