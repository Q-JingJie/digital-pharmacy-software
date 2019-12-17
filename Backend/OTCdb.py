# -*- coding: utf-8 -*-
import MySQLdb

def OTCconnection():
    conn = MySQLdb.connect(host="localhost",
                           user = "user",
                           passwd = "DigitalPharmacY1920",
                           db = "otcmedicine")
    c = conn.cursor()
    return c, conn
		

