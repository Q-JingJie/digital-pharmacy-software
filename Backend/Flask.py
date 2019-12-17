#!/usr/bin/ python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from OTCdb import OTCconnection
from Prescriptiondb import Prescriptionconnection
from Userdb import Userconnection
import gc
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from flask_cors import CORS, cross_origin
from email.mime.base import MIMEBase 
from email import encoders 
#from flask import app


app = Flask(__name__)
CORS(app, support_credentials=True)


MedicineDict = {"Diphenhydramine":{"Diphenhydramine is an antihistamine that dries up secretions. It reduces sputum production and expands the bronchial air passages":"Diphenhydramine 是一种抗过敏药，能使气管里的分泌物变干。它能疝少痍的产生．并有扩张支气管的作用"}}


# information leaflets
files = ['Diphenhydramine.pdf','Insulin.pdf']



@app.route('/PrescriptionMed/' , methods=["GET","POST"])
def PrescriptionMed():
        medicine_data = request.get_json() # Get the user input/qr code from react
                                           # Expecting NRIC and language information from react
                                           
        if medicine_data: 
            c, conn = Userconnection()  # connect to User Medicine database(DB)
            c.execute("select * from users where NRIC = '{}'".format(medicine_data['nric'].upper()))
            medicine_list = c.fetchall() 
            c.close()
            conn.close()
            gc.collect()
            
            
            # # connect to User Medicine database(DB) for available stock and price
            c, conn = Prescriptionconnection()  
            c.execute("select * from stocklist")
            medicine_stock = c.fetchall() 
            c.close()
            conn.close()
            gc.collect()
            
            
            medicines = []
            
            
            if medicine_list: # check there data in medicine_list 
                #pass the medicine data from database to react
                for medicine in medicine_list:
                    medicines.append({'NRIC': medicine[1], 'MedA' : medicine[2], 'MedB' : medicine[3] })
            
                if medicine_stock:
                    for medicine in medicine_stock:
                        medicines.append({'MedAStock':medicine[1], 'MedAPrice':medicine[2], 'MedBStock':medicine[3], 'MedBPrice':medicine[4]})
            
            # pass the medication description to react
                if medicine_data['language'].lower() == 'en': # if the language is english
                    for key, value in MedicineDict.items():
                        if key =='Diphenhydramine': # for now there only 1 medicine description
                            for k,v in value.items():
                                medicines.append({'Diphenhydramine':k})
                
                if medicine_data['language'].lower() == 'ch': # if the language is chinese
                    for key, value in MedicineDict.items():
                        if key =='Diphenhydramine': # for now there only 1 medicine description
                            for k,v in value.items():
                                medicines.append({'Diphenhydramine':v})
       
            return jsonify({'medicines' : medicines}) # pass the josn data to React 
        return('None')
    
     
@app.route('/OTCMedicine/')
@cross_origin(supports_credentials=True)
def OTCMedicine():
    # connect to OTC database(DB)
    c, conn = OTCconnection()
    c.execute("select * from stocklist")
    medicine_list = c.fetchall() 
    c.close()
    conn.close()
    gc.collect()
    
    medicines = []
    # Get all the available medicine from DB to react
    for medicine in medicine_list:
        medicines.append({'Name': medicine[1], 'Stock' : medicine[2], 'Price' : medicine[3]})
    return jsonify({'medicines' : medicines})



def message(num):
    file = files[num]
    filename = file
    attachment = app.open_resource(file, "rb") 
    
    p = MIMEBase('application', 'octet-stream') 
    p.set_payload((attachment).read()) 
    encoders.encode_base64(p) 
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
    return(p)


@app.route('/updateDBPM/', methods=["GET","POST"])# update datebase for prescription med
def updateDBPM():
     medicine_data = request.get_json() # Get the data from react
     # Expecting NRIC, email and quantity of medA and medB brought by customer
     
     try:
         c, conn = Userconnection()   
         c.execute("select * from users where NRIC = '{}'".format(medicine_data['nric'].upper()))
         medicine_list = c.fetchall() 
         c.close()
         conn.close()
         gc.collect()
         
         c, conn = Prescriptionconnection()  
         c.execute("select * from stocklist")
         medicine_stock = c.fetchall() 
         c.close()
         conn.close()
         gc.collect()
         
         #for medicine in medicine_list:
         medAstock = medicine_stock[0][1] - int(medicine_data['medA'])
         medA = medicine_list[0][2] -  int(medicine_data['medA'])
         medBstock = medicine_stock[0][3] - int(medicine_data['medB'])
         medB = medicine_list[0][3] -  int(medicine_data['medB'])
         

         c, conn = Userconnection()   
         sql_update_query = ("update users SET medA = {}, medB = {}, email = '{}' where NRIC = '{}'"
                             .format(medA, medB, medicine_data['email'], medicine_data['nric']))
         c.execute(sql_update_query)
         conn.commit()
         c.close()
         conn.close()
         gc.collect()
         
         c, conn = Prescriptionconnection() 
         sql_update_query = ("update stocklist SET medAstock = {}, medBstock = {} where id = 1"
                             .format(medAstock, medBstock))
         c.execute(sql_update_query)
         conn.commit()
         c.close()
         conn.close()
         gc.collect()
         
            
         # Send email to alert us when stock is low   
         title = ''
         if (medAstock <5 and medBstock<5):
            title = 'Low stock for MedicineA and MedicineB'
         elif medAstock <5:
            title = 'Low stock for MedicineA'
         elif medBstock <5:
            title = 'Low stock for MedicineB'
         if title !='':
            fromaddr = "digitalpharmacy1@gmail.com"
            toaddr = "digitalpharmacy1@gmail.com"
            msg = MIMEMultipart()
            msg['From'] = fromaddr
            msg['To'] = toaddr
            msg['Subject'] = title
    
            body = "Low stock. Please replenish ASAP"
            msg.attach(MIMEText(body, 'plain'))
    
    
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login("digitalpharmacy1@gmail.com", "Pharmacy1920")
            text = msg.as_string()
            server.sendmail(fromaddr, toaddr, text)
            server.quit()
            
        
        
        # Send medications information leaflets to users                
         fromaddr = "digitalpharmacy1@gmail.com"
         toaddr = medicine_data['email']
         msg = MIMEMultipart()
         msg['From'] = fromaddr
         msg['To'] = toaddr
         msg['Subject'] = "Information leaflets"
        
        
         body = "Dear Sir or Madam,\nThanks for using GoMed\nPlease find attached information leaflets for your medications"
         msg.attach(MIMEText(body, 'plain'))
        
        
         if int(medicine_data['medA'])!=0:
            p = message(0)
            msg.attach(p) 
                
         if int(medicine_data['medB'])!=0:
            p = message(1)
            msg.attach(p) 
            
         server = smtplib.SMTP('smtp.gmail.com', 587)
         server.ehlo()
         server.starttls()
         server.ehlo()
         server.login("digitalpharmacy1@gmail.com", "Pharmacy1920")
         text = msg.as_string()
         server.sendmail(fromaddr, toaddr, text)
         server.quit()  
            
         return jsonify('Done')
   
     except Exception as e:
        return ("error")
    


def otcdb(medid, data):
    c, conn = OTCconnection()  
    c.execute("select * from stocklist where id = {}".format(medid))
    medicine_list = c.fetchall() #data from database
    medstock = int(medicine_list[0][2]) - int(data)
    return(medstock)
    
    
@app.route('/updateDBOTC/', methods=["GET","POST"])# update datebase for OTC med
def updateDBOTC():
    medicine_data = request.get_json() # Get the data from react
    # Expecting quantity of MedicineA and MedicineB brought by customer
    
    try:
        MedicineAStock = otcdb(1,medicine_data['medicineA'])
        MedicineBStock = otcdb(2,medicine_data['medicineB'])
         
    
        c, conn = OTCconnection()  
        sql_update_query = ("update stocklist SET medicinestock = {} where id = {}".format(MedicineAStock, 1))
        c.execute(sql_update_query)
        conn.commit()
        sql_update_query = ("update stocklist SET medicinestock = {} where id = {}".format(MedicineBStock, 2))
        c.execute(sql_update_query)
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        
        title = ''
        if (MedicineAStock <5 and MedicineBStock<5):
            title = 'Low stock for MedicineA and MedicineB'
        elif MedicineAStock <5:
            title = 'Low stock for MedicineA'
        elif MedicineBStock <5:
            title = 'Low stock for MedicineB'
        if title!='':
            fromaddr = "digitalpharmacy1@gmail.com"
            toaddr = "digitalpharmacy1@gmail.com"
            msg = MIMEMultipart()
            msg['From'] = fromaddr
            msg['To'] = toaddr
            msg['Subject'] = title

            body = "Low stock. Please replenish ASAP"
            msg.attach(MIMEText(body, 'plain'))


            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login("digitalpharmacy1@gmail.com", "Pharmacy1920")
            text = msg.as_string()
            server.sendmail(fromaddr, toaddr, text)
            server.quit()
            
            
        return jsonify('Done')
    except Exception as e:
        return('error')
    
    
if __name__ == '__main__':
    app.run(debug = True)
    