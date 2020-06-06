import PySimpleGUI as sg  # type: ignore
import time


def delayPopup(delay):
    start = time.time()
    counter = 0

    while time.time() - start < delay:
        layout = [[sg.Text("Attendere", size=(16,1), key="Text")]]

        window = sg.Window("Attendere", layout, keep_on_top=True, size=(200, 80))

        while time.time() - start < delay:
            counter = (counter + 1) % 6
            event, _ = window.Read(timeout=500)

            if event == None:
                break

            window["Text"].Update("Attendere" + "."*counter)
        
        window.close()
