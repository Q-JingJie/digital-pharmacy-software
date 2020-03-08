import serial
import time

class serial_conn:
    def __init__(self, port, baud, time_out, device_name):
        self.port     = port
        self.baudrate = baud
        self.timeout  = time_out
        self.name     = device_name
        Connected = False
        while not Connected:
            try:
                self.ser = serial.Serial(self.port, baudrate = self.baudrate, timeout = self.timeout)
                Connected = True
            except serial.serialutil.SerialException:
                print (self.name, "on", self.port, "is not found")
                time.sleep(1)
        
    def read(self):
        status = "Disconnected\n"
        try:
            status = self.ser.readline().decode()[:-1:]            
        except serial.serialutil.SerialException:
            self.ser.close()
            try:
                while not self.ser.isOpen():
                    time.sleep(self.timeout)
                    self.ser.open()
            except serial.serialutil.SerialException:
                    pass
        except UnicodeDecodeError:
            status = "Decoding Error\n"
        return status

    def set_timeout(self, timeout):
        self.ser.timeout = timeout
        self.timeout = timeout

    def flush(self):
        self.ser.timeout = 0.01
        while user_qr.read() != '':
            pass
        self.ser.timeout = self.timeout

    def write(self, data):
        try:
            self.ser.write(data.encode())
            time.sleep(0.01)
        except serial.serialutil.SerialException:
            pass
    
    def close(self):
        try:
            self.ser.close()
            print(self.name, "on",self.port, "has been closed")
        except:
            print("Error closing", self.name, "on", self.port)
