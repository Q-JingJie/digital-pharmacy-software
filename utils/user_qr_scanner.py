from serial_conn import serial_conn

user_qr = serial_conn("COM5", 115200, 2, "User QR Scanner") #Motion as a serial object

while True:   #May be daemon called by main thread to return a queue instead
    print(user_qr.read())
