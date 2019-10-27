import serial
import time

class qr_scanner:
    def __init__(self, port, baud, time_out):
        self.port     = port
        self.baudrate = baud
        self.timeout  = time_out
        Connected = False
        while (Connected == False):
            try:
                self.ser = serial.Serial(self.port, baudrate = self.baudrate, timeout = self.timeout)
                Connected = True
            except serial.serialutil.SerialException:
                print ("QR Scanner on", self.port, "is not found!")
                time.sleep(self.timeout)

        
    def read(self):
        qr = str("Disconnected")
        try:
            qr = self.ser.readline().decode()[:-2:]            
        except serial.serialutil.SerialException:
            self.ser.close()
            try:
                while (self.ser.isOpen() == False):
                    time.sleep(self.timeout)
                    self.ser.open()
            except serial.serialutil.SerialException:
                    pass
                
        return qr
   

med  = qr_scanner("COM10", 115200, 2)

while (True):
    print (med.read())
