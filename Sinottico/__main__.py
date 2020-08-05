from queue import Queue
import threading
import sys
from io import TextIOBase

from .view.main.main_window import main_window
from .controller.controller import controllerTask
from .controller.arduino import controller_arduino_task


class LazyWriter(TextIOBase):
    def __init__(self, filepath):
        self.filepath = filepath
        self.first = True

    def write(self, stuff):
        mode = "w" if self.first else "a"
        self.first = False
        with open(self.filepath, mode) as f:
            f.write(stuff)


def main():
    sys.stderr = LazyWriter("trace.txt")

    workq: queue.Queue = Queue()
    ardq: queue.Queue = Queue()
    guiq: queue.Queue = Queue()

    t = threading.Thread(target=controllerTask, args=(guiq, workq))
    t.daemon = True
    t.start()

    t = threading.Thread(target=controller_arduino_task, args=(guiq, ardq))
    t.daemon = True
    t.start()

    main_window(workq, ardq, guiq)


if __name__ == '__main__':
    main()
