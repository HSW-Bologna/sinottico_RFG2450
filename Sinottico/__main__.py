from queue import Queue
import threading

from .view.main.main_window import mainWindow
from .controller.controller import controllerTask
from .controller.arduino import controller_arduino_task


def main():
    workq: queue.Queue = Queue()
    ardq: queue.Queue = Queue()
    guiq: queue.Queue = Queue()

    t = threading.Thread(target=controllerTask, args=(guiq, workq))
    t.daemon = True
    t.start()

    t = threading.Thread(target=controller_arduino_task, args=(guiq, ardq))
    t.daemon = True
    t.start()

    mainWindow(workq, ardq, guiq)


if __name__ == '__main__':
    main()