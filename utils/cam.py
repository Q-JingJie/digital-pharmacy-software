import cv2                 #py -m pip install opencv-python
from pyzbar import pyzbar  #py -m pip install pyzbar 
import pytesseract         #py -m pip install pytesseract      install windows binary
import threading
import queue

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
framecount = 0

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def OCR():
    while(True):
        text = pytesseract.image_to_string(q1.get(),config = "--psm 1")
        if len(text) == 0:
            text = "No text string!"
        print(text)

def BARCODE():
    while(True):
        q3.put(pyzbar.decode(q2.get()))

q1 = queue.Queue(maxsize=1)
q2 = queue.Queue(maxsize=1)
q3 = queue.Queue(maxsize=1)

ocr = threading.Thread(target=OCR, args=())
ocr.start()
bar = threading.Thread(target=BARCODE, args=())
bar.start()

while(True):
    ret, frame = capture.read()
    frame1 = cv2.addWeighted(frame,0,frame,1.15,0)
    cv2.imshow('processed', frame1)
    if (q1.empty() == True):
        q1.put(frame1)

    if (q2.empty() == True):
        q2.put(frame)

    if q3.empty() == 1:    
        barcodes = q3.get()
    
        for barcode in barcodes:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)   

    cv2.imshow('video', frame)
    if cv2.waitKey(1) == 27:
        break
 
capture.release()
cv2.destroyAllWindows()
