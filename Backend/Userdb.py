# -*- coding: utf-8 -*-


import MySQLdb

def Userconnection():
    conn = MySQLdb.connect(host="localhost",
                           user = "user",
                           passwd = "DigitalPharmacY1920",
                           db = "userinfo")
    c = conn.cursor()
    return c, conn
		