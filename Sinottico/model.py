from adt import adt, Case


class SerialConfig:
    def __init__(self, port=None, baud=38400, data=8, stop=1, parity="None", flowctrl="None", end="Nessuno"):
        self.port = port
        self.baud = baud
        self.data = data
        self.stop = stop
        self.parity = parity
        self.flowctrl = flowctrl
        self.end = end


@adt
class WorkMessage:
    NEWPORT: Case[SerialConfig]
    SEND: Case[str]


@adt
class GuiMessage:
    RECV: Case[str]
