import RPi.GPIO as GPIO #import RPi.GPIO module
from time import sleep
import adxl345
import I2C_LCD_driver
from threading import Thread
import sys
from mfrc522 import SimpleMFRC522
import subprocess

#===================================IMPORTING REQUESTS====================================#
import requests
import base64
import json
from datetime import datetime

#=====================================Global-Variable=====================================#
PWSet = '12345'
door_state = True
#-----------------------------------------------------------------------------------------#
GPIO.setmode(GPIO.BOARD) #choose BCM mode
GPIO.setwarnings(False)
GPIO.setup(37,GPIO.OUT) #set GPIO 26 as output
PWM=GPIO.PWM(37,50) #set 50Hz PWM output at GPIO26
GPIO.setup(15,GPIO.IN) #set GPIO 22 as input
GPIO.setup(13, GPIO.OUT)
#-----------------------------------------------------------------------------------------#
LCD = I2C_LCD_driver.lcd() #instantiate an lcd object, call it LCD
sleep(0.5)
LCD.backlight(0) #turn backlight off
sleep(0.5)
LCD.backlight(1) #turn backlight on
#-----------------------------------------------------------------------------------------#
sleep(1) #wait 1 sec
LCD.lcd_clear() #clear the display
#-----------------------------------------------------------------------------------------#

acc=adxl345.ADXL345() #instantiate
acc.load_calib_value() #load calib. values in accel_calib
acc.set_data_rate(data_rate=adxl345.DataRate.R_100) #see datasheet
acc.set_range(g_range=adxl345.Range.G_16,full_res=True) # ..
acc.measure_start()
#-----------------------------------------------------------------------------------------#

MATRIX=[ [1,2,3],
         [4,5,6],
         [7,8,9],
         ['*',0,'#']] #layout of keys on keypad

ROW=[31,38,35,33] #row pins
COL=[32,29,36] #column pins

#set column pins as outputs, and write default value of 1 to each
for i in range(3):
    GPIO.setup(COL[i],GPIO.OUT)
    GPIO.output(COL[i],1)

#set row pins as inputs, with pull up
for j in range(4):
    GPIO.setup(ROW[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)
#-----------------------------------------------------------------------------------------#

#-----------------------------------------------------------------------------------------#
def send_data(status):#Send Data To The Server
    now = datetime.now().strftime("%m-%d-%Y,%H;%M;%S")
    url = "https://------------------.herokuapp.com/upload" #insert server url here(I used heroku. You can use whichever you want.)
    GPIO.output(13,1)
    subprocess.run(["fswebcam", "./static/"+now+".jpg"])
    image = open("./static/" +now+".jpg", "rb").read()
    base64_encoded_data = base64.b64encode(image)
    base64_message = base64_encoded_data.decode("utf-8")
    myobj = {"status": status, "image": base64_message, "date": now}
    myobj = json.dumps(myobj)
    x = requests.post(url, data=myobj)
    print(x)
    GPIO.output(13,0)

#-----------------------------------------------------------------------------------------#
def DoorLock(state):#Change Door State
    if state:
        PWM.start(3) #3% duty cycle
        LCD.lcd_clear() #clear the display
        LCD.lcd_display_string("Door Locked!", 1)
        LCD.lcd_display_string("Goodbye!", 2)
        print("Door Locked! Duty Cycle: 3") #3 o'clock position
        sleep(1) #allow time for movement
        LCD.lcd_clear() #clear the display
        LCD.lcd_display_string("Insert password:", 1) #write on line 1
        
    else:
        PWM.start(12) #3% duty cycle
        LCD.lcd_clear() #clear the display
        LCD.lcd_display_string("Door Unlocked!", 1)
        LCD.lcd_display_string("Welcome!", 2)
        print("Door Unlocked! Duty Cycle: 12") #3 o'clock position
        send_data(status[1])
        sleep(1) #allow time for movement

#-----------------------------------------------------------------------------------------#
def AccDoorCheck():#Check Accelerometer
    global door_state
    while True:
        x,y,z = acc.get_3_axis_adjusted()
        #print(z) #z: 0.01 - 0.05 safe
        sleep(0.1)

        if z > 0.3 or z < -0.3:     #accelerometer picks up movement
            if door_state:              #door is locked, therefore force opening is detected
                #take pic
                #send notif
                #server send info
                send_data(status[0])
                print("Something happens " + str(z))
            else:                       #door is unlocked, therefore door is not being forcefully opened
                #nothing? not sure
                print("Nothing happens")

#-----------------------------------------------------------------------------------------#
def PWInputCheck():#Check Password
    global door_state
    PWUser = ''
    PWUserChar = ''
    #global door_state
    #DoorLock(door_state)
    
    while 1:
        
        for i in range(3): #loop thru’ all columns
            GPIO.output(COL[i],0) #pull one column pin low
            for j in range(4): #check which row pin becomes low
                if GPIO.input(ROW[j])==0: #if a key is pressed
                    PWUserChar = str(MATRIX[j][i])
                    PWUser += PWUserChar
                    LCD.lcd_display_string(PWUser, 2) #write on line 2
                    
                    while GPIO.input(ROW[j])==0: #debounce
                        sleep(0.1)
            GPIO.output(COL[i],1) #write back default value of 1
        """
        #if RFID triggers a 1:
            #repeat same as door unlock
        """    
        
        if len(PWUser) == len(PWSet):
            if PWUser == PWSet:    #password is correct
                print("Door is unlocked! Password is Correct!")
                PWUser=''
                door_state = False
                DoorLock(door_state)
    
            elif PWUser != PWSet:  #password is incorrect
                print("Door still locked! Password is Wrong!")
                PWUser=''
                    
                LCD.lcd_display_string("Wrong Password", 2)
                sleep(0.2)
                LCD.lcd_display_string("              ", 2)
                sleep(0.2)
                LCD.lcd_display_string("Wrong Password", 2)
                sleep(0.2)
                LCD.lcd_display_string("              ", 2)
                sleep(0.2)
                LCD.lcd_display_string("Wrong Password", 2)
                sleep(0.5)
           
                LCD.lcd_clear() #clear the display

# -----------------------------------------------------------------------------------------#
def RFIDInputCheck():#Check RFID Card Reader
    global door_state
    reader = SimpleMFRC522()
    auth = []
    f = open("authlist.txt", "r+")
    if f.mode == "r+":
        auth=f.read()
    while 1:
        print("Hold card near the reader to check if it is in the database")
        id = reader.read_id()
        id = str(id)
        

        if id in auth:#Find Card Number in Authorisation
              number = auth.split('\n')
              pos = number.index(id)

              door_state = False
              DoorLock(door_state)

            
              print("Card with UID", id, "found in database entry #", pos, "; access granted")
        else:
              print("Card with UID", id, "not found in database; access denied")
        sleep(0.3)


#-----------------------------------------------------------------------------------------#
def slideswitch():#Locks Door After Switch is Pressed
    global door_state
    while(True): #loop
        if GPIO.input(15): #if read a high at GPIO 22
            door_state = True
            DoorLock(door_state)
        else: #otherwise (i.e. read a low) at GPIO 22
            pass
        sleep(3) # to limit print() frequency


#-----------------------------------------------------------------------------------------#
door_state = True
status = ["break in", "normal"]#door status array
DoorLock(door_state)#lock door

#-----------------------------------------------------------------------------------------#


#-------------------------------------Threading Loops-------------------------------------#
Thread(target=AccDoorCheck).start()     #Check Accelerometer
Thread(target=PWInputCheck).start()     #Check Password
Thread(target=RFIDInputCheck).start()   #Check RFID Card Reader
Thread(target=slideswitch).start()      #Locks Door After Switch is Pressed
#-----------------------------------------------------------------------------------------#

