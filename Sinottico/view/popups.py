import PySimpleGUI as sg  # type: ignore
import time
import re


def popupTimedCancel(title, text, delay, key="Cancel"):
    start = time.time()
    layout = [[sg.Text(text)], [sg.Button(key, size=(16, 1), key=key)]]
    window = sg.Window(title, layout, keep_on_top=True)

    while True:
        event, _ = window.Read(timeout=0.1)
        if event == key:
            window.close()
            return key
        elif event == None:
            return None

        if time.time() - start > delay:
            window.close()
            return None


def delayPopup(delay):
    start = time.time()
    counter = 0

    while time.time() - start < delay:
        layout = [[sg.Text("Attendere", size=(16, 1), key="Text")]]

        window = sg.Window("Attendere",
                           layout,
                           keep_on_top=True,
                           size=(200, 80))

        while time.time() - start < delay:
            counter = (counter + 1) % 6
            event, _ = window.Read(timeout=500)

            if event == None:
                break

            window["Text"].Update("Attendere" + "." * counter)

        window.close()


def adjustPopup(value):
    oldvalue = str(value)
    layout = [[sg.Text("Compensare il valore rilevato:")],
              [
                  sg.Spin([x / 10. for x in range(5, 100, 5)],
                          initial_value=0.5,
                          size=(3, 1),
                          key="S"),
                  sg.Text("Step")
              ],
              [
                  sg.Button("-", size=(4, 1), key="-"),
                  sg.Input(str(value),
                           size=(12, 1),
                           change_submits=True,
                           key="T"),
                  sg.Button("+", size=(4, 1), key="+")
              ], [sg.Button("OK", key="OK", bind_return_key=True)]]
    window = sg.Window("Compensazione",
                       layout,
                       keep_on_top=True,
                       return_keyboard_events=True)

    while True:
        event, values = window.Read()

        try:
            if event in (None, "OK"):
                window.close()
                return float(window["T"].Get())
            elif event == "T":
                newvalue = re.sub("[^0-9]", "", values[event])
                fvalue = float(newvalue)
                window["T"].Update(newvalue)
                oldvalue = newvalue
            elif event in ["-", "Down:116", "minus:20"]:
                x = float(values["T"])
                s = values["S"]
                if x - s >= 0:
                    window["T"].Update("{:.2f}".format(x - s))
                else:
                    window["T"].Update("{:.2f}".format(0.))
            elif event in ["+", "Up:111", "plus:21"]:
                x = float(values["T"])
                s = values["S"]
                window["T"].Update("{:.2f}".format(x + s))
        except ValueError:
            window["T"].Update(oldvalue)


def yesNoPopup(text):
    layout = [[sg.Text(text)],
              [
                  sg.Button("NO", size=(16, 1), key="NO"),
                  sg.Button("SI", size=(16, 1), key="SI")
              ]]
    window = sg.Window("Conferma",
                       layout,
                       return_keyboard_events=True,
                       keep_on_top=True)

    while True:
        event, _ = window.Read()
        if event in ["SI", "y:29", "Y:29"]:
            window.close()
            return True
        elif event in [None, "NO", "n:57", "N:57"]:
            window.close()
            return False
