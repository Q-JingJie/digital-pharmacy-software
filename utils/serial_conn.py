import serial
import time

class serial_conn:
    def __init__(self, port, baud, time_out, device_name):
        self.port     = port
        self.baudrate = baud
        self.timeout  = time_out
        self.name     = device_name
        Connected = False
        while (Connected == False):
            try:
                self.ser = serial.Serial(self.port, baudrate = self.baudrate, timeout = self.timeout)
                Connected = True
            except serial.serialutil.SerialException:
                print (self.name, "on", self.port, "is not found!")
                time.sleep(self.timeout)
        
    def read(self):
        status = "Disconnected\n"
        try:
            status = self.ser.readline().decode()[:-1:]            
        except serial.serialutil.SerialException:
            self.ser.close()
            try:
                while (self.ser.isOpen() == False):
                    time.sleep(self.timeout)
                    self.ser.open()
            except serial.serialutil.SerialException:
                    pass
        except UnicodeDecodeError:
            status = "Decoding Error\n"
        return status

    def write(self, data):
        try:
            self.ser.write(data.encode())
            time.sleep(0.01)
        except serial.serialutil.SerialException:
            pass
