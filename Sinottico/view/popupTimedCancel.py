import PySimpleGUI as sg  # type: ignore
import time


def popupTimedCancel(title, text, delay, key="Cancel"):
    start = time.time()
    layout = [[sg.Text(text)], [sg.Button(key, size=(16,1), key=key)]]
    window = sg.Window(title, layout, keep_on_top=True)

    while True:
        event, _ = window.Read(timeout = 0.1)
        if event == key:
            window.close()
            return key
        elif event == None:
            return None

        if time.time() - start > delay:
            window.close()
            return None
