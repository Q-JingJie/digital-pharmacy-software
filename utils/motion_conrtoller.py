from serial_conn import serial_conn
from inventory import inventory
import time
import cv2
import os

#++++++++++++++ PHYSICAL CONSTRAINTS +++++++++++++
X_MAX = 900                                 #Maxmium travel length on X axis
Y_MAX = 130                                 #Maxmium travel length on Y axis
Z_MAX = 750                                 #Maxmium travel length on Z axis
DISPENSING_LOCATION = 800                   #Location of dispensing box, based on X axis

X_CARRIAGE_WIDTH = 80                       #Size of X carriages. Set to a slightly larger value to prevent collision due to inaccuracy in measuerments.
X_LEFT_OFFSET = 40                           #Offset value to center X left carrriage
X_RIGHT_OFFSET = 42                          #Offset value to center X right carrriage

X_MAX_TRAVEL = X_MAX - X_CARRIAGE_WIDTH     #Actual allowed travel distance, limited by the two carriages

DEBUG = True
IMAGE_PATH = "C:/Users/Janson/Desktop/Capture"

#++++++++++++++ SERIAL COMMUNICATIONS +++++++++++++
motion = serial_conn("COM10", 115200, 0.1, "Motion Controller") #Motion as a serial object
med_qr = serial_conn("COM2", 115200, 0.1, "Medicine QR Scannerr") #Motion as a serial object


capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


#++++++++++++++ MOTION +++++++++++++
def motor_enable(state): #Enable is not required. Stepper motor should be disabled when not needed.
    if state == True:
        motion.write("M17\r")
    else:
        motion.write("M18\r")
    return True if motion.read()== "ok\r" else False


def stepper_home_position():
    motion.write("G28\r")
    homing = True
    while homing:
        result = motion.read()
        if result != '':
            homing = False
    return False if ("ERROR" in result) or ("!!" in result) else True


def position_sanity_check(x_left, x_right, y, z):  #Check for XYZ boundaries, as well as platform collision
    if (y > Y_MAX) or (y < 0) or (z > Z_MAX) or (z < 0) or (x_left > X_MAX_TRAVEL) or (x_left < 0) or (x_right > X_MAX_TRAVEL) or (x_right < 0) or ((x_right - x_left) < X_CARRIAGE_WIDTH):
        return False
    else:
        return True

    
def stepper_set_position(x_left, x_right, y, z, blocking):  #While the position is being set, only the read/set position commands should be executed.
    if position_sanity_check(x_left, x_right, y, z) == True: #The execution of other commands result in the inability to read realtime position.
        current_x_left, current_x_right, current_y, current_z = x_left, x_right, y, z
        x_right_corrected = X_MAX_TRAVEL - x_right  #Map value of X_right to actual Y axis output
        motion.write("G1 X" + str("%.2f" % x_left) + " Y" + str("%.2f" % x_right_corrected)  + " Z" + str("%.2f" % z) + " E" + str("%.2f" % y) + " F20000\r")
        result = True if motion.read()== "ok" else False
        while blocking:
            reading = stepper_read_realtime_position()
            if reading != None:
                if (abs(reading[0] - x_left) < 0.1) and (abs(reading[1] - x_right) < 0.1) and (abs(reading[2] - y)< 0.1) and (abs(reading[3] - z) < 0.1):
                    blocking = False
        return result


def stepper_read_realtime_position():  #Read actual position and returns [X_LEFT, X_RIGHT, Y, Z]
    motion.write("M114.3\r")
    position = motion.read().split()
    if len(position) == 6:
        return  [float(position[2][2::]), round((X_MAX_TRAVEL - float(position[3][2::])),4), float(position[5][2::]), float(position[4][2::])]
    else:
        return None


def stepper_read_set_position():  #Read set position and returns [X_LEFT, X_RIGHT, Y, Z]
    motion.write("M114\r")
    position = motion.read().split()
    if len(position) == 6:
        return  [float(position[2][2::]), round((X_MAX_TRAVEL - float(position[3][2::])),4), float(position[5][2::]), float(position[4][2::])]
    else:
        return None
    

def Y_axis_angle(angle):         #for 180 degrees servo, mapped 0 to 180 degrees to PWM.
    if (angle <= 180) and (angle >= 0):
        angle = "%.2f" % (angle/180.0 * 5.0 + 5.0)
        motion.write("M280.1 S" + angle + "\r")
    else:
        motion.write("M281.1\r") #If angle is out of range(0,180), the servo motor is turned off.
    return True if motion.read()== "ok\r" else False



#++++++++++++++ PERIPHERAL +++++++++++++
def vacuum_pump_enable(state):#Vacuum and solenoid can be controlled via PWM (S command)
    if state == True:
        motion.write("M110.1\r")
    else:
        motion.write("M111.1\r")
    return True if motion.read()== "ok\r" else False

def LED_enable(state):        #LED can be controlled via PWM (S command)
    if state == True:
        motion.write("M110.2 S100\r")
    else:
        motion.write("M111.2\r")
    return True if motion.read()== "ok\r" else False


def fan_enable(state):        #Fan can be controlled via PWM (S command)
    if state == True:
        motion.write("M106\r")
    else:
        motion.write("M107\r")
    return True if motion.read()== "ok\r" else False



#++++++++++++++ SYSTEM +++++++++++++
def soft_reset():     #Reset
    motion.write("M999\r")
    result = motion.read()
    motion.read()
    return True if (result == "ok\r") or (result == "WARNING: After HALT you should HOME as position is currently unknown") else False

def system_halt():    #On system halt, soft reset or reset is required to exit state
    motion.write("M112\r")
    return True if motion.read() == "ok Emergency Stop Requested - reset or M999 required to exit HALT state\r" else False



#++++++++++++++ OPTIMIZERS +++++++++++++
def collection_order(medicine_list_raw): #Start from bottom left
    medicine_list = []
    medicine_list_sorted = sorted(medicine_list_raw, key=lambda x: (x[4], -x[3]))

    for medicine in medicine_list_sorted:
        for i in range(0, medicine[2]):
            medicine_list.append([medicine[0], medicine[1], medicine[3], medicine[4], medicine[5]])
    return medicine_list


def stepper_set_position_optimized(x_left, x_right, y, z): #optimize X_left and X_right platform position by allowing more time for QR scanner when possible
    if position_sanity_check(x_left, x_right, y, z) == True:
        waiting = True
        
        while waiting:
            result = stepper_read_set_position()
            if result != None:
                [current_x_left, current_x_right, current_y, current_z] = result
                waiting = False
                
        delta_x_left  = abs(x_left  - current_x_left)
        delta_x_right = abs(x_right - current_x_right)
        delta_z       = abs(z - current_z)
        
        if(delta_x_left > 0.1) and (delta_z < 0.1):
            if delta_x_left < delta_x_right:
                if (x_right - current_x_right) > 0:
                    stepper_set_position(x_left, current_x_right + delta_x_left, y, z, True)
                else:
                    stepper_set_position(x_left, current_x_right - delta_x_left, y, z, True)
            else:
                if (x_left - current_x_left) > 0:
                    stepper_set_position(current_x_left + delta_x_right, x_right, y, z, True)
                else:
                    stepper_set_position(current_x_left - delta_x_right, x_right, y, z, True)
                
        return stepper_set_position(x_left, x_right, y, z, True)



#++++++++++++++ VERIFICATION AND IMAGING +++++++++++++
def verification (medicine_name, timeout):
    done = False
    start = time.time()
    
    while done == False:
        if med_qr.read() == medicine_name:
            done = True
            return True

        if (time.time() - start) > timeout:
            done = True
    return False

def image(medicine_name):
    ret, frame = capture.read()
    return cv2.imwrite(os.path.join(IMAGE_PATH, time.strftime("%Y%m%d_%H%M%S_") + medicine_name + ".png"), frame)



    
#++++++++++++++ COLLECTION +++++++++++++
def collection(medicine_list_raw):
    #stepper_home_position()
    LED_enable(False)
    vacuum_pump_enable(False)
    Y_axis_angle(30)
    
    medicine_list = collection_order(medicine_list_raw)       #Reoganise medicine list for optimal collection
    max_index = len(medicine_list) - 1

    
    #Collection Sequencer
    for index, medicine in enumerate(medicine_list):
        #Move QR platfom to the medicine location, and the collection platform beside it.
        x_left = medicine[2] - X_LEFT_OFFSET
        x_right = x_left + X_CARRIAGE_WIDTH
        y = 0
        z = medicine[3]
        print("Verifying medicine", index + 1, medicine[0], x_left, x_right, y, z, end=' ')
        result = stepper_set_position_optimized(x_left, x_right, y, z) 
        print(result)

        
        #veification sequence & image capturing
        result = verification(medicine[0],5)
        print("Medicine", medicine[0],"verified" , result)
        print(image(medicine[0]))

        
        #Move QR platfom to the next medicine location if possible, otherwise beside the collection platform. Moves collection platform to the medicine location 
        x_right = medicine[2] - X_RIGHT_OFFSET
        
        if index < max_index:
            if medicine_list[index + 1][2] < x_left:
               x_left = medicine_list[index + 1][2] - X_LEFT_OFFSET
            else:
                x_left = x_right - X_CARRIAGE_WIDTH
        else:
            x_left = x_right - X_CARRIAGE_WIDTH
        print("Collecting medicine", x_left, x_right, y, z, end=' ')
        result = stepper_set_position_optimized(x_left, x_right, y, z)
        print(result)
        
        
        #Turn on vacuum pump and valve to collect medicine
        result = vacuum_pump_enable(True)
        print("Vacuum pump enabled", result)
        y = Y_MAX
        print("Extending linear actuator", x_left, x_right, y, z, end=' ')
        result =  stepper_set_position(x_left, x_right, y, z, True)  #Extend Y axis to extract medicine
        print(result)
        

        if medicine[4] != 0:
            z = medicine[3] + medicine[4]
            result = stepper_set_position(x_left, x_right, y, z, True)  #Lift Z axis if required, as specified in the medicine list
            print("Performing Z lift", x_left, x_right, y, z, result)
        
        y = 0
        print("Retracting linear actuator", x_left, x_right, y, z, end=' ')
        result = stepper_set_position(x_left, x_right, y, z, True)  #Retract Y axis to extract medicine
        print(result)
        
        if index < max_index:
            x_left = medicine_list[index + 1][2] - X_LEFT_OFFSET
        x_right = DISPENSING_LOCATION
        z = medicine[3]
        print("Moving to dispenser", x_left, x_right, y, z, end=' ')
        result = stepper_set_position_optimized(x_left, x_right, y, z) # Move to dispensing location
        print(result)

        if medicine[1] == "bottle":
            result = Y_axis_angle(90)                                    #Move Y axis to drop position
            print("Moving Y axis servo", result)
            y = Y_MAX
            print("Extending linear actuator", x_left, x_right, y, z, end=' ')
            result = stepper_set_position(x_left, x_right, y, z, True)         #Extend Y axis to drop medicine
            print(result)
            result = vacuum_pump_enable(False)                           #Turn off vacuum pump, dropping the medicine
            print("Vacuum pump disabled, medicine released", result)
            print("Retracting linear actuator", x_left, x_right, y, z, end=' ')
            result = stepper_set_position(x_left, x_right, y, z, True)         #Retract Y axis
            print(result)
            result = Y_axis_angle(30)                                    #Move Y axis to collection position
            print("Moving Y axis sevo", result)
        else:
            result = vacuum_pump_enable(False)                           #Turn off vacuum pump, dropping the medicine
            print("Vacuum pump disabled", result)

    #After collection
    result = Y_axis_angle(-1)                                                             #Turn off servo motor
    print("Y axis servo disabled", result)
    #stepper_home_position()                                                      #Move platform to home position
    result = motor_enable(False)                                                          #Disable all motors
    print("Stepper motors disabled", result)
    result = LED_enable(True)                                                             #Indicates that it is ready for collection
    print("LED enabled", result)
    time.sleep(5)
    result = LED_enable(False)
    print("LED disabled", result)
