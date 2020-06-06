
import PySimpleGUI as sg  # type: ignore


def adjustPopup(value):
    layout = [[sg.Text("Compensare il valore rilevato:")],
                [sg.Spin([x/10. for x in range(1, 10)], size=(3, 1), key="S"), sg.Text("Step")],
                [sg.Button("-", size=(4,1), key="-"), sg.Input(str(value), size=(12,1), key="T", disabled=True), sg.Button("+", size=(4,1), key="+")],
                [sg.Button("OK", key="OK", bind_return_key=True)]]
    window = sg.Window("Compensazione", layout, keep_on_top=True)

    while True:
        event, values = window.Read()

        if event in (None, "OK"):
            window.close()
            return float(window["T"].Get())
        elif event == "-":
            x = float(values["T"])
            s = values["S"]
            if x - s >= 0:
                window["T"].Update("{:.2f}".format(x - s))
            else:
                window["T"].Update("{:.2f}".format(0.))
        elif event == "+":
            x = float(values["T"])
            s = values["S"]
            window["T"].Update("{:.2f}".format(x + s))



