import sqlite3
db_location = r'C:\Users\DP\Desktop\FlaskApp\pythonsqlite.db'
conn = sqlite3.connect(db_location)
cursor = conn.execute("SELECT * from prescriptionmed where nric = 'XXX'")
medicine_list = cursor.fetchall()

#sql_update_query = ("update prescriptionmed SET quantity = 1 where DBid = 1")
#conn.execute(sql_update_query)       
#conn.commit()



db_location = r'C:\Users\DP\Desktop\FlaskApp\pythonsqlite.db'
conn = sqlite3.connect(db_location)
cursor = conn.execute("SELECT * from prescriptionstock")
medicine_stock = cursor.fetchall() 


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
print(json)
        

##
##        
##
##json['medicines'] = medicines
##
##print(json)
##
