import time
from serial_conn import serial_conn


#time.sleep(5)
print("time up")
from flask import Flask,jsonify,request

from flask_cors import CORS, cross_origin
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import random
from playsound import playsound
import threading
from email import encoders
from email.mime.base import MIMEBase
from motion_controller import collection
user_qr = serial_conn("COM3", 115200, 1, "User QR Scanner")
random.seed(0)

db_location = r'C:\Users\DP\Desktop\FlaskApp\pythonsqlite.db'
#db_location = r'C:\Users\Kan Chee Kong\Desktop\FlaskApp1\pythonsqlite.db'
app = Flask(__name__)
CORS(app, support_credentials=True)


#initialise the medication location
med_location = {}
med_location['Diphenhydramine'] = ['bottle',520,0]





@app.route('/management/' , methods=["GET","POST"])
def management():
    conn = sqlite3.connect(db_location) # need change file location
    cursor = conn.execute("SELECT * from otcmedicine")
    medicine_list = cursor.fetchall()   


    c = conn.execute("SELECT * from prescriptionstock")
    medicine_stock = c.fetchall()
    conn.close()
    medicines = []
    # Get all the available medicine from DB to react
    for medicine in medicine_list:
    #    medicines.append({'Name': medicine[1], 'Stock' : medicine[2], 'Price' : medicine[3]})
         medicines.append({'id': medicine[0], 'name' : medicine[1], 'stock' : medicine[2], 'brand': medicine[6]})

    for medicine in medicine_stock:
        medicines.append({'id': medicine[0], 'name' : medicine[1], 'stock' : medicine[4], 'brand': medicine[2]})

    return jsonify({'medicines' : medicines})



def otclist(medid, data):
    conn = sqlite3.connect(db_location)
    cursor = conn.execute("SELECT * from otcmedicine where medid = {}".format(medid))
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[medid][2]) + int(data)
    return(medstock)


def Plist(medname, data):
    conn = sqlite3.connect(db_location)
   # qr = 'XXX'
    cursor = conn.execute("SELECT * from prescriptionstock where PmedName = '{}'".format(medname)) # need change
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[0][4]) - int(data)
    return(medstock)


@app.route('/updatemaindb/' , methods=["GET","POST"])
def updatemaindb():
    updatemed = request.get_json()
    print(updatemed)
    conn = sqlite3.connect(db_location) # need change file location
    
    for item in (updatemed["medicines"]):
        try:
            if 'p' not in str(item['id']):
                sql_update_query = ("update otcmedicine SET medicinestock = {} where medid = {}".format(item['stock'], item['id']))
                conn.execute(sql_update_query)       
                conn.commit()
            else:
                sql_update_query = ("update prescriptionstock SET PMedStock = {} where medid = '{}'".format(item['stock'], item['id']))
                conn.execute(sql_update_query)       
                conn.commit()
                
        except Exception as e:
            print(e)
            return jsonify('false')
            
    return jsonify('done')
                    
    

def securitycode():
    global securityCode
    securityCode = random.randint(100000,999999)
    title = 'Security Code'
    fromaddr = "digitalpharmacy1@gmail.com"
    toaddr = "digitalpharmacy1@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = title

    body = "Your OTP is {}. Use it within 1 minutes before it expires.".format(securityCode)
    msg.attach(MIMEText(body, 'plain'))


    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login("digitalpharmacy1@gmail.com", "Pharmacy1920")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    


@app.route('/qrcode/' , methods=["GET","POST"])
def qrcode():
    start_scanning = request.get_json()

    try: 
        if start_scanning['qr']:
            print('scanning now')
            global qr
            qr = user_qr.read()
            print (qr)
            if qr =='':
                print("no QR code detected")
                return jsonify('Failed')
            elif qr!='':
            #if qr != '':
                playsound(r'C:\Users\DP\Desktop\FlaskApp\beep.mp3')  # need change location'
                #securitycode()
                t1 = threading.Thread(target=securitycode) 
                t1.start()
                print('QR code detected')
                return jsonify('True')
    except Exception as e:
        print(e)
        return jsonify('false')
    


@app.route('/PMed/' , methods=["GET","POST"])
def PMed():
    qr = 'XXX'
    try:
        conn = sqlite3.connect(db_location)
        cursor = conn.execute("SELECT * from prescriptionmed where nric = '{}'".format(qr.strip()))
        medicine_list = cursor.fetchall()   

        c = conn.execute("SELECT * from prescriptionstock")
        medicine_stock = c.fetchall()
        conn.close()

        medicines = []
        json = {}
        json['NRIC'] = medicine_list[0][1]
        medlist = {}

        for i in range(len(medicine_list)):
            for j in range(len(medicine_stock)):
                if (medicine_list[i][2] == medicine_stock[j][0]):
                    medlist["dbid"] = medicine_list[i][0]
                    medlist["id"] = medicine_list[i][2]
                    medlist["name"] = medicine_stock[j][1]
                    medlist["brand"] = medicine_stock[j][2]
                    medlist["description"] = medicine_stock[j][3]
                    medlist["stock"] = medicine_stock[j][4]
                    medlist["price"] = medicine_stock[j][5]
                    medlist["qty"] = medicine_list[i][3]
                    medicines.append(medlist)
                    medlist = {}

        json["medicine"] = medicines
        return jsonify({'medicines' : json})
        
    except Exception as e:
        print(e)
        return jsonify('Problem accessing database')




def Pdb(medid, data):
    conn = sqlite3.connect(db_location)
   # qr = 'XXX'
    cursor = conn.execute("SELECT * from prescriptionmed where DBid = '{}'".format(medid)) # need change
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[0][3]) - int(data)
    return(medstock)


def Pstock(medname, data):
    conn = sqlite3.connect(db_location)
   # qr = 'XXX'
    cursor = conn.execute("SELECT * from prescriptionstock where PmedName = '{}'".format(medname)) # need change
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[0][4]) - int(data)
    return(medstock)

def message(med):
    extension = '.pdf'
    file = 'Diphenhydramine.pdf'
    #file = med +extension
    filename = file
    attachment = open(file, "rb") 
    
    p = MIMEBase('application', 'octet-stream') 
    p.set_payload((attachment).read()) 
    encoders.encode_base64(p) 
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
    return(p)
    
def Pemail(med):
    fromaddr = "digitalpharmacy1@gmail.com"
    toaddr = 'digitalpharmacy1@gmail.com'
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Information leaflets"
    
    
    body = "Dear Sir or Madam,\nThanks for using GoMed\nPlease find attached information leaflets for your medications"
    msg.attach(MIMEText(body, 'plain'))
    
    
    p = message(med)
    msg.attach(p) 
    ##    
    ##
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login("digitalpharmacy1@gmail.com", "Pharmacy1920")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()  
    
@app.route('/updateDBPmed/', methods=["GET","POST"])# update datebase for OTC med
def updateDBPmed():
    medicine_data = request.get_json() # Get the data from react
    print(medicine_data)  # debugging
    # Expecting quantity of Medicine brought by customer
    # test out later
    
##    try:
    cart = medicine_data["cart"]
    conn = sqlite3.connect(db_location) 
    for item in cart:
             
           try:
                remainingstock = Pdb(item['dbid'], item['qty'])
                sql_update_query = ("update prescriptionmed SET quantity = {} where DBid = {}".format(remainingstock, item['dbid']))
                conn.execute(sql_update_query)       
                conn.commit()

                remainingstock = Pstock(item['name'], item['qty'])
                sql_update_query = ("update prescriptionstock SET PMedStock = {} where PmedName = ''".format(remainingstock, item['name']))
                conn.execute(sql_update_query)       
                conn.commit()

                if int(remainingstock) < 15:
                    t2 = threading.Thread(target=otcStockEmail , args=(item['name'],))            
                    t2.start()

                t3 = threading.Thread(target=Pemail , args=(item['name'],))            
                t3.start()
              
            

                # call function to activate hardware
                conn.close()
                return jsonify('Done')
           except Exception as e:
                print(e)
                return('error')
        






@app.route('/PrescriptionMed/' , methods=["GET","POST"])
def PrescriptionMed():
    pin = request.get_json()
    FA = []
    for i in range(len(str(securityCode))):
        FA.append(int(str(securityCode)[i]))
    print(FA, pin)
    if FA == pin:
        return jsonify('True')
    else:
       return jsonify('Wrong code')


@app.route('/OTCMedicine/')
@cross_origin(supports_credentials=True)
def OTCMedicine():
    # connect to OTC database(DB)
    conn = sqlite3.connect(db_location) # need change file location
    cursor = conn.execute("SELECT * from otcmedicine")
    medicine_list = cursor.fetchall()   
    conn.close()
    
    medicines = []
    # Get all the available medicine from DB to react
    for medicine in medicine_list:
    #    medicines.append({'Name': medicine[1], 'Stock' : medicine[2], 'Price' : medicine[3]})
         medicines.append({'id': medicine[0], 'name' : medicine[1], 'stock' : medicine[2], 'description': medicine[4], 'cost' : "{:.2f}".format(medicine[3]),
         "pic": r"http://157.245.196.149/static/images/{}".format(medicine[5]), 'brand': medicine[6]})
    

    return jsonify({'medicines' : medicines})
    
    



def otcdb(medid, data):
    conn = sqlite3.connect(db_location)
    cursor = conn.execute("SELECT * from otcmedicine where medid = {}".format(medid))
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[0][2]) - int(data)
    return(medstock)


    
def otcStockEmail(stock):
     title = 'Low stock for {}'.format(stock)
     fromaddr = "digitalpharmacy1@gmail.com"
     toaddr = "digitalpharmacy1@gmail.com"
     msg = MIMEMultipart()
     msg['From'] = fromaddr
     msg['To'] = toaddr
     msg['Subject'] = title

     body = "Low stock for {}. Please replenish ASAP".format(stock)
     msg.attach(MIMEText(body, 'plain'))


     server = smtplib.SMTP('smtp.gmail.com', 587)
     server.ehlo()
     server.starttls()
     server.ehlo()
     server.login("digitalpharmacy1@gmail.com", "Pharmacy1920")
     text = msg.as_string()
     server.sendmail(fromaddr, toaddr, text)
     server.quit()


@app.route('/paymentOTC/', methods=["GET","POST"])# update datebase for OTC med
def paymentOTC():
    global paymentResult
    paymentResult = random.randint(1,10)
    if paymentResult ==6:
        random.seed(0)
        return jsonify({'transactionPass':True})
    else:
        return jsonify({'transactionPass':False})
     
     
@app.route('/updateDBOTC/', methods=["GET","POST"])# update datebase for OTC med
def updateDBOTC():
    medicine_data = request.get_json() # Get the data from react
    # Expecting quantity of Medicine brought by customer
    print(medicine_data)  # debugging
    #medicine_list = [["Diphenhydramine", "box", 1 , 465, 0]]
    #             ["Diphenhydramine", "blister", 1 , 152, 235],
    #             ["Diphenhydramine", "blister", 1 , 250, 235],
    #             ["Diphenhydramine", "blister", 1 , 333, 235],
    #             ["Diphenhydramine", "blister", 1 , 425, 235],
    #             ["Diphenhydramine", "blister", 1 , 512, 235]]
                 
    medicine_list = []    
   # medicine_list.append([item['name'],med_location[item['name']][0],item['quantity'],med_location[item['name']][1],med_location[item['name']][2]])
    collection(medicine_list)
    try:
        cart = medicine_data["cart"]
        print(cart)
        conn = sqlite3.connect(db_location) 
        for item in cart:
            medicine_list.append([item['name'],med_location[item['name']][0],item['quantity'],med_location[item['name']][1],med_location[item['name']][2]])
            collection(medicine_list)
          #  print(item['id'])
            remainingstock = otcdb(item['id'], item['quantity'])
            sql_update_query = ("update otcmedicine SET medicinestock = {} where medid = {}".format(remainingstock, item['id']))
            conn.execute(sql_update_query)       
            conn.commit()
            print('updated')  
            medicine_list = []    
            if int(remainingstock) < 15:
               # otcStockEmail(item['name'])
               t2 = threading.Thread(target=otcStockEmail , args=(item['name'],))            
               t2.start()
            
            # call function to activate hardware
        conn.close()
        return jsonify('Done')
    except Exception as e:
        print(e)
        return('error')
        
        
        
        
if __name__ == '__main__':
    try:
       
        app.run(debug = False)
    except KeyboardInterrupt:
        print("LALALALAL")
        user_qr.close()