from serial_conn import serial_conn
import time
import cv2
import os
from numpy import cos


#++++++++++++++ PHYSICAL CONSTRAINTS +++++++++++++
X_MAX = 741                                         #Maxmium travel length on X axis
Y_MAX = 76                                          #Maxmium travel length on Y axis
Z_MAX = 750                                         #Maxmium travel length on Z axis

X_CARRIAGE_WIDTH = 90                               #Size of X carriages with inflation
X_LEFT_OFFSET    = -18                              #Offset value to center X left carrriage
X_RIGHT_OFFSET   = 28                               #Offset value to center X right carrriage
Z_OFFSET         = 0                                #Offset value to Z axis height
Y_ANGLE = 26                                        #Collection angle

DISPENSING_LOCATION = X_MAX - 5                     #Location of dispensing box, based on X axis
BIN_LOCATION = 60                                   #Location of bin box, based on X axis
MAX_RELEASE_HEIGHT  = 100                           #Global maximum height for medicine release

Z_LIFT = 150                                        #Lift Z axis if it is a bottle or box
Z_FREE = 150                                        #Height where the collection platform is able to rotate medicine without obstacle
Y_FREE = 0                                          #Distance where the collection platform is able to rotate medicine without obstacle
Y_RETRACT_WHILE_Z_LIFT = Z_LIFT * cos(Y_ANGLE * 0.01745) #Retract Y axis linearly with Z lift

SERVO_30_DEG = 69                                   #Upwards
SERVO_0_DEG  = 90                                   #Horizontal
SERVO_10_DEG  = 110                                 #Downwards
SERVO_90_DEG = 160                                  #Downwards

DEFAULT_FEEDRATE = 12000                            #Normal Speed
Y_ACTUATOR_FEEDRATE = 5000                          #Y actuator collection speed
MAX_FEEDRATE = 20000                                #Feedrate for X only moves
MAX_RETRIES = 3                                     #Number of retries allowed for collection

                         


#++++++++++++++ SERIAL COMMUNICATIONS +++++++++++++
motion = serial_conn("COM4", 115200, 0.2, "Motion Controller")
med_qr = serial_conn("COM2", 115200, 0.1, "Medicine QR Scanner")
QR_VERIFICATION_TIMEOUT = 5
NO_STOCK = 'Out of Stock'




#++++++++++++++ CAMERA INITIALIZATION +++++++++++++
capture = cv2.VideoCapture(1)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
IMAGE_PATH = "D:/Capture"





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
    if (y > Y_MAX) or (y < 0) or (z > Z_MAX) or (z < 0) or (x_left > X_MAX) or (x_left < 0) or (x_right > X_MAX) or (x_right < 0) or ((x_right - x_left) < X_CARRIAGE_WIDTH):
        return False
    else:
        return True

    
def stepper_set_position(x_left, x_right, y, z, blocking, feedrate = DEFAULT_FEEDRATE):  #While the position is being set, only the read/set position commands should be executed.
    if position_sanity_check(x_left, x_right, y, z) == True: #The execution of other commands result in the inability to read realtime position.
        x_right_corrected = X_MAX - x_right  #Map value of X_right to actual Y axis output
        motion.write("G1 X" + str("%.2f" % x_left) + " Y" + str("%.2f" % x_right_corrected)  + " Z" + str("%.2f" % z) + " E" + str("%.2f" % y) + " F" + str(feedrate) + "\r")
        result = True if motion.read()== "ok" else False

        while blocking:
            reading = stepper_read_realtime_position()
            if reading != None:
                if (abs(reading[0] - x_left) < 0.1) and (abs(reading[1] - x_right) < 0.1) and (abs(reading[2] - y)< 0.1) and (abs(reading[3] - z) < 0.1):
                    blocking = False
                    
        return result


def stepper_read_realtime_position():  #Read actual position and returns [X_LEFT, X_RIGHT, Y, Z]
    motion.flush()

    try:
        motion.write("M114.3\r")
        position = motion.read().split()
        if len(position) == 6:
            return  [float(position[2][2::]), round((X_MAX - float(position[3][2::])),4), float(position[5][2::]), float(position[4][2::])]
        else:
            return None
    except:
        return None

'''
def stepper_read_set_position():  #Read set position and returns [X_LEFT, X_RIGHT, Y, Z]
    motion.write("M114\r")
    position = motion.read().split()
    if len(position) == 6:
        return  [float(position[2][2::]), round((X_MAX - float(position[3][2::])),4), float(position[5][2::]), float(position[4][2::])]
    else:
        return None
'''    

def Y_axis_angle(angle):         #for 180 degrees servo, mapped 0 to 180 degrees to PWM.
    if (angle <= 180) and (angle >= 0):
        angle = "%.2f" % (angle/180.0 * 9.0 + 3.3)
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
        motion.write("M110.2\r")
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
            medicine_list.append([medicine[0], medicine[1], medicine[3], medicine[4]])
    return medicine_list

'''
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
'''




#++++++++++++++ VERIFICATION AND IMAGING +++++++++++++
def verification (medicine_name):
    med_qr.flush()
    start = time.time()
    
    while True:
        qr_text = med_qr.read()
        print(qr_text)
        if qr_text == medicine_name:
            return True
        elif qr_text == NO_STOCK:
            return None
        
        if (time.time() - start) > QR_VERIFICATION_TIMEOUT:
            return False


def capture_image(medicine_name):
    ret, frame = capture.read()
    return cv2.imwrite(os.path.join(IMAGE_PATH, time.strftime("%Y%m%d_%H%M%S_") + medicine_name + ".png"), frame)




    
#++++++++++++++ COLLECTION +++++++++++++
def collection(medicine_list):
    motion.flush()
    
    #Home all axis on startup   
    stepper_home_position()

    #Set collection actuator angle
    Y_axis_angle(SERVO_30_DEG)

    #Configure peripherals
    fan_enable(True)            #Stepper cooling
    LED_enable(False)           #Turn off collection box LED
    vacuum_pump_enable(False)   #Turn off vacuum pump
    
    #Reoganise medicine list for optimal collection
    medicine_list = collection_order(medicine_list)
    max_index = len(medicine_list) - 1
    
    #Variables
    retries = 0
    out_of_stock = []
    unverified = []
    
    for index, medicine in enumerate(medicine_list):
        #STEP 0
        #If too many retries have been attepmted
        if retries > MAX_RETRIES:
            break

        #If medicine is previously marked as out of stock
        #Then no point checking again
        if len(out_of_stock) != 0:
            if out_of_stock[-1] == medicine[0]:
                continue
            
        while True:
            #STEP 1
            #Move QR platfom to the medicine location, and the collection platform to its side
            x_left = medicine[2] + X_LEFT_OFFSET
            x_right = x_left + X_CARRIAGE_WIDTH
            y = 0
            z = medicine[3] + Z_OFFSET 
            stepper_set_position(x_left, x_right, y, z, True) 


            #STEP 2        
            #QR verification & capture image
            verification_result = verification(medicine[0]) #True: Verified     #False: Unverified     #None: Out of stock
            capture_image(medicine[0])

            if verification_result is None:
                out_of_stock.append(medicine[0])
                break

            if not verification_result:
                unverified.append(medicine[0])
                retries += 1

                
            #STEP 3
            #Move collection platform to the medicine location         
            x_right = medicine[2] + X_RIGHT_OFFSET
            x_left = x_right - X_CARRIAGE_WIDTH
            stepper_set_position(x_left, x_right, y, z, False, feedrate = MAX_FEEDRATE)


            #STEP 4        
            #Turn on vacuum pump and valve to collect medicine
            vacuum_pump_enable(True)


            #STEP 5
            #Extend linear actuator to extract medicine
            y = Y_MAX
            stepper_set_position(x_left, x_right, y, z, True, feedrate = Y_ACTUATOR_FEEDRATE)
            time.sleep(0.1)
                 
            #STEP 6
            #If it is a bottle or box, remove by lifting Z axis and retracting Y axis linearly
            if medicine[1] == "bottle" or medicine[1] == "box":
                z += Z_LIFT
                y -= Y_RETRACT_WHILE_Z_LIFT     
                stepper_set_position(x_left, x_right, y, z, False, feedrate = Y_ACTUATOR_FEEDRATE)

            #STEP 6.5
            #Retract Y axis completely to extract medicine
            y = 0
            stepper_set_position(x_left, x_right, y, z, True, feedrate = Y_ACTUATOR_FEEDRATE)


            #STEP 7        
            #Move QR platform to the next medicine location
            #Move collection platform to the medicine location
            #Move Z lower than maximum release height, or z lift height if it is a bottle
            if index < max_index:
                x_left = medicine_list[index + 1][2] + X_LEFT_OFFSET

            if verification_result:
                x_right = DISPENSING_LOCATION
            else:
                x_right = BIN_LOCATION

            if medicine[1] == "bottle":
                z = Z_FREE
            else:
                if z > MAX_RELEASE_HEIGHT:
                    z = MAX_RELEASE_HEIGHT
                
            result = stepper_set_position(x_left, x_right, y, z, True)


            #STEP 8
            #If it is a bottle, move Y axis slightly forward and rotate bottle downwards
            #Extend Y axis and lower Z axis to dampen drop
            #Then retract Y axis and assume collection angle
            if medicine[1] == "bottle":
                y = Y_FREE
                stepper_set_position(x_left, x_right, y, z, True)
                time.sleep(0.1)
                Y_axis_angle(SERVO_90_DEG)
                time.sleep(0.3)
                y = Y_MAX
                z = 0
                stepper_set_position(x_left, x_right, y, z, True)
                vacuum_pump_enable(False)
                time.sleep(0.3)
                y = 0
                stepper_set_position(x_left, x_right, y, z, True)
                time.sleep(0.3)
                Y_axis_angle(SERVO_30_DEG)

            #If it is not a bottle, ie box, blister etc
            #Disable vacuum pump and flick the medicine off the collection platform
            else:
                vacuum_pump_enable(False)
                Y_axis_angle(SERVO_10_DEG)
                time.sleep(0.5)
                Y_axis_angle(SERVO_30_DEG)

            if verification_result:
                break
            
            if retries > MAX_RETRIES:
                break

    #END COLLCETION
    #Collection has finished, home axis
    #Turn on ready indication LED, wait for 10s
    LED_enable(True)
    stepper_home_position()
    fan_enable(False)
    time.sleep(5)

    #After 5s, disable motor and LED
    motor_enable(False)
    
    #After 10s, disable motor and LED
    time.sleep(5)
    LED_enable(False)

    return out_of_stock, unverified
