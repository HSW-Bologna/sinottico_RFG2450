from queue import Queue
import threading
import sys
from io import TextIOBase

from .view.main.main_window import main_window
from .controller.controller import controllerTask
from .controller.arduino import controller_arduino_task


class LazyWriter(TextIOBase):
    def __init__(self, filepath):
        self.file = None
        self.filepath = filepath

    def write(self, stuff):
        if not self.file:
            self.file = open(self.filepath, "w")
        self.file.write(stuff)

    def __del__(self):
        if self.file:
            self.file.close()


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
