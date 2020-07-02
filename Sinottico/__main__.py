from queue import Queue
import threading

from .view.main.main import mainWindow
from .controller.controller import controllerTask

def main():
    workq: queue.Queue = Queue()
    guiq: queue.Queue = Queue()

    t = threading.Thread(target=controllerTask, args=(guiq, workq))
    t.daemon = True
    t.start()

    mainWindow(workq, guiq)

if __name__ == '__main__':
    main()