# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 18:23:00 2020

@author: Kan Chee Kong
"""

import pysftp

# cnopts = pysftp.CnOpts()
# cnopts.hostkeys = None
# srv = pysftp.Connection(host="157.245.196.149", username="root",
# password="DigitalpharmacY1920",cnopts=cnopts)

# with srv.cd('/var/www/FlaskApp/Database/'): #chdir to public
    # srv.put(r'C:\Users\DP\Desktop\FlaskApp\pythonsqlite.db') #upload file to nodejs/

# Closes the connection
# srv.close()

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
with pysftp.Connection(host="157.245.196.149", username="root",password="DigitalpharmacY1920",cnopts=cnopts) as sftp:

     remoteFilePath = '/var/www/FlaskApp/Database/pythonsqlite.db'
     localFilePath = r'C:\Users\DP\Desktop\FlaskApp\dip.db'

     sftp.get(remoteFilePath, localFilePath)
