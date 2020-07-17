import sys
import glob
import serial  # type: ignore
from ..model import *

def serialPorts(avoid=[]):
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            if not port in avoid:
                s = serial.Serial(port)
                s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result




def connect_to_port(c: SerialConfig):
    bytesize = {8: serial.EIGHTBITS}[c.data]
    parity = {
        'None': serial.PARITY_NONE,
        'Even': serial.PARITY_EVEN,
        'Odd': serial.PARITY_ODD
    }[c.parity]
    stop = {
        1: serial.STOPBITS_ONE,
        1.5: serial.STOPBITS_ONE_POINT_FIVE,
        2: serial.STOPBITS_TWO
    }[c.stop]
    return serial.Serial(port=c.port,
                         baudrate=c.baud,
                         bytesize=bytesize,
                         parity=parity,
                         stopbits=stop,
                         timeout=0.2)
