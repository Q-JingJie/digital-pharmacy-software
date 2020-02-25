import time
from serial_conn import serial_conn
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
import datetime
#from motion_controller import collection


#user_qr = serial_conn("COM3", 115200, 0.2, "User QR Scanner")
random.seed(0)

#db_location = r'C:\Users\DP\Desktop\FlaskApp\pythonsqlite.db'
db_location = r'E:\FlaskApp1\FlaskApp\pythonsqlite.db'
app = Flask(__name__)
CORS(app, support_credentials=True)


#initialise the medication location
med_location = {}
med_location['Diphenhydramine'] = ['bottle',521,0]
med_location['MedicineB'] = ["blister",192, 235]
med_location['MedicineC'] = ["blister",290, 235]
med_location['MedicineD'] = ["blister",373, 235]
med_location['MedicineE'] = ["blister",465, 235]
med_location['MedicineF'] = ["blister",552, 235]
med_location['MedicineG'] = ["blister",82, 235]
med_location['MedicineH'] = ["blister",652, 235]
med_location['MedicineI'] = ["box",501, 0]


#medicine_list = [["Diphenhydramine", "box", 1 , 465, 0]]
#             ["Diphenhydramine", "blister", 1 , 152, 235],
#             ["Diphenhydramine", "blister", 1 , 250, 235],
#             ["Diphenhydramine", "blister", 1 , 333, 235],
#             ["Diphenhydramine", "blister", 1 , 425, 235],
#             ["Diphenhydramine", "blister", 1 , 512, 235]]





@app.route('/startingpage/' , methods=["GET","POST"])
def startingpage():
    #time.sleep(1)
    playsound(r'C:\Users\DP\Desktop\FlaskApp\beep.mp3') 
    playsound(r'C:\Users\DP\Desktop\FlaskApp\welcome.mp3') # need change address
    return jsonify('True')

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



@app.route('/updatemaindb/' , methods=["GET","POST"])
def updatemaindb():
    updatemed = request.get_json()
    print(updatemed)
    conn = sqlite3.connect(db_location) # need change file location
    
    try:
        for item in (updatemed["medicines"]):
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
                    
 
# generate security code
@app.route('/securitycode/' , methods=["GET","POST"])
def securitycode():
    global securityCode
    securityCode = random.randint(100000,999999)
    title = 'Security Code for Cuboid Digital Pharmacy'
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
    return jsonify('True')
    

@app.route('/flushqr/' , methods=["GET","POST"])
def flushqr():
    while user_qr.read() != '':
        pass
    return jsonify('True')





# 2FA verification
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




@app.route('/qrcode/' , methods=["GET","POST"])
def qrcode():
    time.sleep(1)
    start_scanning = request.get_json()
    print(start_scanning)
    global qr
    try: 
         if start_scanning['qr']:
             print('scanning now')            
             qr = ''            
             while (qr == ''):
                qr = user_qr.read()
             print (qr)
             playsound(r'C:\Users\DP\Desktop\FlaskApp\beep.mp3')  # need change location'
             playsound(r'C:\Users\DP\Desktop\FlaskApp\beep2.mp3') 
             if qr.strip() == 'Diclofenac Sodium 25mg':
                print('management page')              
                return jsonify('manage')
             elif qr != '':
                 print('QR code detected')
                 return jsonify('True')
             else:
                return jsonify('error')
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
        med = {}
        med['NRIC'] = medicine_list[0][1]
        medlist = {}

        for i in range(len(medicine_list)):
            for j in range(len(medicine_stock)):
                if (medicine_list[i][2] == medicine_stock[j][0]) and (medicine_list[i][4]!= medicine_list[i][3]):
                    medlist["dbid"] = medicine_list[i][0]
                    medlist["id"] = medicine_list[i][2]
                    medlist["name"] = medicine_stock[j][1]
                    medlist["brand"] = medicine_stock[j][2]
                    medlist["description"] = medicine_stock[j][3]
                    medlist["stock"] = medicine_stock[j][4]
                    medlist["price"] = medicine_stock[j][5]
                    medlist["qty"] = medicine_list[i][3]
                    medlist["collected"] = medicine_list[i][4]
                    medlist["Instruction"] = medicine_list[i][5]
                    medlist["pic"] = r"http://157.245.196.149/static/images/{}".format(medicine_stock[j][6])
                    medicines.append(medlist)
                    medlist = {}


        med["medicine"] = medicines
        return jsonify({'medicines' : med})
        
    except Exception as e:
        print(e)
        return jsonify('Problem accessing database')




def Pdb(medid, data):
    conn = sqlite3.connect(db_location)
    cursor = conn.execute("SELECT * from prescriptionmed where DBid = '{}'".format(medid)) # need change
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[0][4]) + int(data)
    return(medstock)


def Pstock(medname, data):
    conn = sqlite3.connect(db_location)
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
    
def Pemail(brochure, invoice):
    title = 'Cuboid Digital Pharmacy Invoice'
    fromaddr = "digitalpharmacy1@gmail.com"
    toaddr = 'digitalpharmacy1@gmail.com'
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = title
    
    item = ''
    line = '-'
    for items in range(0,len(invoice)-1,5):
        item = item+"{}                        {}                       {}\n{}\n{}\n{}\n".format(medlist[items],medlist[items+1],medlist[items+2],medlist[items+3],medlist[items+4],line*70)
    
    total = "                                         Total Amount paid: {}".format(medlist[len(invoice)-1])
    body = """\
    <html>
        <body>
            <h2 style="color:grey;"><font size="10">Dear Sir or Madam,</font></h2>
            <h2 style="color:grey;"><font size="10"> Thanks for using Cuboid Digital Pharmacy</font></h2>
            <h3 style="color:grey;"><font size="8">  Your {}/{}/{} invoice is now available.</font></h3>
            <br>
            <h3><center><font size="8">Prescription Summary</font></center></h3>
            <br>
            <h3><pre><font size="6">Drugs/Presctiption                 Quantity                 Amount(S$)</font></pre></h3>
            <h3><pre><font size="6">{}</font></pre></h3><br>
            <h3><pre style="border:1px solid black;"><font size="6">{}</font></pre><h3>
            <h3> Please find attached information leaflets for your medications </h3>
            <h3> Have question? </h3>
            <h3> You can check out our <a href = #>FAQ</a> or our <a href = #>support page for more information</a>
        </body>
    </html>
""".format(now.day, now.month, now.year, item,total)
   
   # body = "Dear Sir or Madam,\nThanks for using GoMed\nPlease find attached information leaflets for your medications"
    msg.attach(MIMEText(body, 'html'))
    
    for item in brochure:
        p = message(item)
        msg.attach(p) 

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login("digitalpharmacy1@gmail.com", "Pharmacy1920")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()  


    
@app.route('/updateDBPmed/', methods=["GET","POST"])# update datebase for prescription med
def updateDBPmed():
    medicine_data = request.get_json() # Get the data from react
    print(medicine_data)  # debugging
    # Expecting quantity of Medicine brought by customer
    # test out later
    
    
    brochure = []
    invoice_item = []
    medicine_list = []    
    try:
        cart = medicine_data["cart"]
        conn = sqlite3.connect(db_location) 
        for item in cart:
            print(item)
            remainingstock = Pdb(item['dbid'], item['qty'])
            sql_update_query = ("update prescriptionmed SET collected = {} where DBid = {}".format(remainingstock, item['dbid']))
            conn.execute(sql_update_query)       
            conn.commit()

            remainingstock = Pstock(item['name'], item['qty'])
            sql_update_query = ("update prescriptionstock SET PMedStock = {} where PmedName = '{}'".format(remainingstock, item['name']))
            conn.execute(sql_update_query)       
            conn.commit()
            
            brochure.append(item['name'])
            invoice_item.extend([item['name'],item['qty'],item['price'],item['description'],item['Instruction']])
            
            if int(remainingstock) < 15:
                t2 = threading.Thread(target=StockEmail , args=(item['name'],))     
                t2.start()                  
            
            
                # call function to activate hardware
            medicine_list.append([item['name'],med_location[item['name']][0],item['qty'],med_location[item['name']][1],med_location[item['name']][2]])
        
           
        conn.close()
        
        # check if email subscription is true
        t3 = threading.Thread(target=Pemail , args=(brochure,invoice_item))    
        t3.start()         
        collection(medicine_list)
        t3.join()
        
        
        
        return jsonify('Done')
    except Exception as e:
         print(e)
         return('error')
        









# list of all GSL medicine
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
    
    


# update GSL database after payment
def otcdb(medid, data):
    conn = sqlite3.connect(db_location)
    cursor = conn.execute("SELECT * from otcmedicine where medid = {}".format(medid))
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[0][2]) - int(data)
    return(medstock)



# email for low stock   
def StockEmail(stock):
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
    time.sleep(5)
    return jsonify('True')


     
# update stock for GSL medicine     
@app.route('/updateDBOTC/', methods=["GET","POST"])# update datebase for OTC med
def updateDBOTC():
    medicine_data = request.get_json() # Get the data from react
    # Expecting quantity of Medicine brought by customer
    print(medicine_data)  # debugging
    medicine_list = []    
    try:
        cart = medicine_data["cart"]
        print(cart)
        conn = sqlite3.connect(db_location) 
        for item in cart:
            remainingstock = otcdb(item['id'], item['quantity'])
            sql_update_query = ("update otcmedicine SET medicinestock = {} where medid = {}".format(remainingstock, item['id']))
            conn.execute(sql_update_query)       
            conn.commit()
            
            
            print('updated')  
            
            
            if int(remainingstock) < 15:
               #otcStockEmail(item['name'])
               t4 = threading.Thread(target=StockEmail , args=(item['name'],))  
               t4.start()
            
            medicine_list.append([item['name'],med_location[item['name']][0],item['quantity'],med_location[item['name']][1],med_location[item['name']][2]])
        if len(medicine_list) != 0:
            collection(medicine_list)
           
            # call function to activate hardware
        conn.close()
        return jsonify('Done')
    except Exception as e:
        print(e)
        return('error')
        
        
        
        
if __name__ == '__main__':
    try:   
        app.run(debug = True)
    except KeyboardInterrupt:
        print("interrupt")
        user_qr.close()

