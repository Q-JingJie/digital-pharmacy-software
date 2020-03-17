from motion_controller import collection
import time

                #["NAME", "UNIT", QUANTITY, X_POSITION, Z_POSITION] 
medicine_list = [["Diphenhydramine", "bottle", 10 , 581, 0],
                 ["Diphenhydramine", "blister", 1 , 152, 235],
                 ["Diphenhydramine", "blister", 1 , 250, 235],
                 ["Diphenhydramine", "blister", 1 , 333, 235],
                 ["Diphenhydramine", "blister", 1 , 425, 235],
                 ["Diphenhydramine", "blister", 1 , 512, 235]]

start = time.time()
collection(medicine_list)
print(time.time() - start)
