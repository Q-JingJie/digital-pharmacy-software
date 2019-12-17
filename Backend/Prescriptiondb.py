# -*- coding: utf-8 -*-

import MySQLdb

def Prescriptionconnection():
    conn = MySQLdb.connect(host="localhost",
                           user = "user",
                           passwd = "DigitalPharmacY1920",
                           db = "prescriptionmed")
    c = conn.cursor()
    return c, conn
		
