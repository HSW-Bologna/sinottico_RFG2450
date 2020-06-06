import PySimpleGUI as sg  # type: ignore
import time


def yesNoPopup(text):
    layout = [[sg.Text(text)], [sg.Button("NO", size=(16,1), key="NO"), sg.Button("SI", size=(16,1), key="SI")]]
    window = sg.Window("Conferma", layout, return_keyboard_events=True, keep_on_top=True)

    while True:
        event, _ = window.Read()
        if event in ["SI", "y:29", "Y:29"]:
            window.close()
            return True
        elif event in [None, "NO", "n:57", "N:57"]:
            window.close()
            return False