import serial

ser = serial.Serial("COM5", baudrate=115200, timeout=0.01)

while(True):
    ser.write(b"M106\n")
    text = ser.read(1000)

    if b'ok' in text:
        print (text[3::])
