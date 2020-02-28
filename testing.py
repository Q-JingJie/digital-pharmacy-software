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
from motion_controller import collection



user_qr = serial_conn("COM3", 115200, 200, "User QR Scanner")


start_collecting = False
finish_collecting = False

app = Flask(__name__)
CORS(app, support_credentials=True)



#initialise the Database location
db_location = r'C:\Users\DP\Desktop\FlaskApp\pythonsqlite.db'
#db_location = r'E:\FlaskApp1\FlaskApp\pythonsqlite.db'



#initialise the medication location
med_location = {}
med_location['Medicine F 10mg'] = ['bottle',521,0]
med_location['Medicine G 20mg'] = ["blister",192, 235]
med_location['Medicine H 30mg'] = ["blister",290, 235]
med_location['Medicine I 40mg'] = ["blister",373, 235]
med_location['Medicine A 100mg'] = ["blister",465, 235]
med_location['Medicine B 200mg'] = ["blister",552, 235]
med_location['Medicine C 300mg'] = ["blister",82, 235]
med_location['Medicine D 400mg'] = ["blister",652, 235]
med_location['Medicine E 500mg'] = ["box",461, 0]



@app.route('/startingpage/' , methods=["GET","POST"])
def startingpage():
    # play welcome to Cuboid Digital Pharmacy
    playsound(r'C:\Users\DP\Desktop\FlaskApp\beep.mp3') 
    playsound(r'C:\Users\DP\Desktop\FlaskApp\welcome.mp3') # need change address
    return jsonify('True')
    


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




@app.route('/flushqr/' , methods=["GET","POST"])
def flushqr():
    user_qr.set_timeout(0.01)
    #global user_qr
    #user_qr.close()
    #user_qr = serial_conn("COM3", 115200, 0.1, "User QR Scanner")
    while user_qr.read() != '':
        pass
        
    user_qr.set_timeout(200)
   # user_qr.close()
    #user_qr = serial_conn("COM3", 115200, 1, "User QR Scanner")
    return jsonify('True')
    
    
    

@app.route('/qrcode/' , methods=["GET","POST"])
def qrcode():
    time.sleep(1)
    #start_scanning = request.get_json()
    #print(start_scanning)
    global qr
    try: 
         #if start_scanning['qr']:
         print('scanning now')            
         qr = ''   
         meds = {}
         while (qr == ''):
            #print(user_qr)
            qr = user_qr.read()
         print (qr)
         playsound(r'C:\Users\DP\Desktop\FlaskApp\beep.mp3')  # need change location'
         playsound(r'C:\Users\DP\Desktop\FlaskApp\beep2.mp3') 
         if qr.strip() == 'Inventory Management':
            print('management page')              
            return jsonify('manage')
         elif qr != '':
            try:
                conn = sqlite3.connect(db_location)
                cursor = conn.execute("SELECT * from prescriptionmed where qrcode = '{}'".format(qr.strip()))
                medicine_list = cursor.fetchall()   
                meds['NRIC'] = medicine_list[0][1]
                print('QR code detected')
                return jsonify('True')
            except Exception as e:
                print(e)
                return jsonify('Problem accessing database')
         else:
            return jsonify('error')
    except Exception as e:
         print(e)
         return jsonify('false')
         


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
    



@app.route('/PMed/' , methods=["GET","POST"])
def PMed():
    #qr = 'XXX'
    #print(qr)
    try:
        conn = sqlite3.connect(db_location)
        cursor = conn.execute("SELECT * from prescriptionmed where qrcode = '{}'".format(qr.strip()))
        medicine_list = cursor.fetchall()   

        c = conn.execute("SELECT * from prescriptionstock")
        medicine_stock = c.fetchall()
        conn.close()

        medicines = []
        med = {}
        med['NRIC'] = medicine_list[0][1]
        med['PrescriptionID'] = medicine_list[0][5]
        med['ValidDate'] = medicine_list[0][6]
        med['Email'] = True
        medlist = {}
        #print('test')
        for i in range(len(medicine_list)):
            for j in range(len(medicine_stock)):
                if (medicine_list[i][2] == medicine_stock[j][0]):
                    medlist["dbid"] = medicine_list[i][0]
                    medlist["id"] = medicine_list[i][2]
                    medlist["name"] = medicine_stock[j][1]
                    medlist["brand"] = medicine_stock[j][2]
                    text = (medicine_stock[j][3]).split("#")
                    
                    medlist["description"] = '{}\n{}'.format(text[0],text[1])
                    print(medlist["description"])
                    medlist["stock"] = medicine_stock[j][4]
                    medlist["price"] = medicine_stock[j][5]
                    medlist["quantity"] = medicine_list[i][3]
                    medlist["collected"] = medicine_list[i][4]
                    #medlist["Instruction"] = medicine_list[i][5]
                    medlist["pic"] = r"http://157.245.196.149/static/images/{}".format(medicine_stock[j][6])
                    #medlist["PrescriptionID"] = medicine_list[i][6]
                  #  medlist["Valid Date"] = medicine_list[i][7]
                    medicines.append(medlist)
                    medlist = {}


        med["medicine"] = medicines
        return jsonify({'medicines' : med})
        
    except Exception as e:
        print(e)
        return jsonify('Problem accessing database')
        


@app.route('/paymentOTC/', methods=["GET","POST"])# update datebase for OTC med
def paymentOTC():
    time.sleep(5)
    return jsonify('True')





def Pdb(medid, data):
    conn = sqlite3.connect(db_location)
    cursor = conn.execute("SELECT * from prescriptionmed where DBid = '{}'".format(medid)) # need change
    medicine_list = cursor.fetchall()    #data from database
    medstock = int(medicine_list[0][4]) + int(data)
    print(medstock, 'medstock')
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


#<h2 style="color:grey;"><font size="8"> Thanks for using Cuboid Digital Pharmacy</font></h2>
#            <h3 style="color:grey;"><font size="8">  Your {}/{}/{} invoice is now available.</font></h3>    
def Pemail(brochure, invoice):
    print('invoice',invoice)
    title = 'Cuboid Digital Pharmacy Invoice'
    fromaddr = "digitalpharmacy1@gmail.com"
    toaddr = 'digitalpharmacy1@gmail.com'
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = title
    
    now = datetime.datetime.now()
    item = ''
    space = ' '
    line = '-'
    total = 0
    for items in range(0,len(invoice)-1,5):
        item = item+"{}{}{}{}{}\n{}\n{}\n".format(invoice[items],(42 - len(invoice[items]))*space,invoice[items+1],(37 - len(str(invoice[items+1])))*space,invoice[items+2],invoice[items+3],line*105)
        total = total + invoice[items+4]
    
    #total = "                                         Total Amount paid: {}".format(invoice[len(invoice)-1])
    print(item)
    total = "                                                            Total Amount paid: ${:.2f}".format(total)
    body = """\
    <html>
        <body>
            <h2><font size="6">Dear Sir or Madam,</font></h2>
            <h2><font size="6">Thanks for using Cuboid Digital Pharmacy</font></h2>
            <h2><font size="6">Your {}/{}/{} invoice is now available.</font></h2>
            <br>
            <h3><center><font size="8">Prescription Summary</font></center></h3>
            <br>
            <h3><pre><font size="6">Drugs/Presctiption                     Quantity                              Amount(S$)</font></pre></h3>
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



@app.route('/finishcollection/', methods=["GET","POST"])    
def finishcollection():
    global finish_collecting
    if finish_collecting == True:
        finish_collecting = False
        return jsonify('Done')
    else:
        return jsonify('Still collecting medicine')
    

# update stock for GSL medicine     
@app.route('/updateDBOTC/', methods=["GET","POST"])# update datebase for OTC med
def updateDBOTC():
    global finish_collecting,start_collecting
    if start_collecting != True:
        start_collecting = True
        medicine_data = request.get_json() # Get the data from react
        # Expecting quantity of Medicine brought by customer
      #  print('react calling')
        print(medicine_data)  # debugging
        medicine_list = []    
        brochure = []
        invoice_item = []
        try:
            cart = medicine_data["cart"]
           # print(cart)
            conn = sqlite3.connect(db_location) 
            
            try:
                #print(cart[0]['Email'])
                for item in cart:
                    if item['purchasing'] !=0:
                        
                        
                        remainingstock = Pdb(item['dbid'], item['purchasing'])
                        sql_update_query = ("update prescriptionmed SET collected = {} where DBid = {}".format(remainingstock, item['dbid']))
                        conn.execute(sql_update_query)       
                        conn.commit()
                        
                        
                        Premainingstock = Pstock(item['name'], item['purchasing'])
                        sql_update_query = ("update prescriptionstock SET PMedStock = {} where PmedName = '{}'".format(Premainingstock, item['name']))
                        conn.execute(sql_update_query)       
                        conn.commit()
                        
                        
                        brochure.append(item['name'])
                        #print(item['name'],item['purchasing'],item['price'],item['Instruction'],item['description'])
                        #invoice_item.extend([item['name'],item['purchasing'],item['price'],item['description'],item['Instruction'],item['subtotal']])
                        print(item['name'],item['purchasing'],item['price'],item['description'])
                        invoice_item.extend([item['name'],item['purchasing'],item['price'],item['description'],item['subtotal']])
                        
                        print(remainingstock, 'remainingstock')
                        if int(Premainingstock) < 15:
                            t2 = threading.Thread(target=StockEmail , args=(item['name'],))     
                            t2.start()                  
                        
                        medicine_list.append([item['name'],med_location[item['name']][0],item['purchasing'],med_location[item['name']][1],med_location[item['name']][2]])
                        
                    
                if (cart[0]['Email']):
                    t5 = threading.Thread(target=Pemail , args=(brochure,invoice_item))    
                    t5.start()         
                   # collection(medicine_list)
                    #t3.join()
                    
            except:
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
                print(medicine_list)
                A3 = threading.Thread(target=collection , args=(medicine_list,))    
                A3.start()     
                #collection(medicine_list)
               
                # call function to activate hardware
            conn.close()
            A3.join()
            try:
                t5.join()
            except:
                pass
            start_collecting = False
            finish_collecting = True
            return jsonify('Done')
    
    
        except Exception as e:
            print(e)
            return('error')
        
        
        
    
        

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
        print('test')
        cart = medicine_data["cart"]
        conn = sqlite3.connect(db_location) 
        for item in cart:
            print(item['dbid'])
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
        





        
        
        
        
if __name__ == '__main__':
    try:   
        app.run(debug = False)
    except KeyboardInterrupt:
        print("interrupt")
        user_qr.close()