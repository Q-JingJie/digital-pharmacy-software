from motion_conrtoller import collection
import time

                #["NAME", "UNIT", QUANTITY, X_POSITION, Z_POSITION, Z_LIFT] 
medicine_list = [["Diphenhydramine", "bottle", 2, 700, 0, 50],
                 ["Paracetamol", "box", 3, 100, 600, 0],
                 ["VX", "bottle", 2, 300, 0, 50],
                 ["Agent Orange", "bottle", 2, 721, 0, 50],
                 ["Plan B", "blister", 4, 400, 100, 0]]

start = time.time()
collection(medicine_list)
print(time.time() - start)
