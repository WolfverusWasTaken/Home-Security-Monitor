import RPi.GPIO as GPIO #import RPi.GPIO module
from time import sleep
import adxl345
import I2C_LCD_driver
from multiprocessing import Process
import sys
import threading

PWSet = '123456'

def AccDoorCheck():
    while true:
        x,y,z = acc.get_3_axis_adjusted()
        #print(z) #z: 0.01 - 0.05 safe
        sleep(0.1)

        if z > 0.3 or z < -0.3:     #accelerometer picks up movement
            if door_state:              #door is locked, therefore force opening is detected
                #take pic
                #send notif
                #server send info
                print("Something happens " + str(z))
            else:                       #door is unlocked, therefore door is not being forcefully opened
                #nothing? not sure
                print("Nothing happens")
                    
        

def PWInputCheck():
    
    PWUser = ''
    PWUserChar = ''
    
    global door_state
    door_check()
    
    while 1:
        #scan keypad
        for i in range(3): #loop thru’ all columns
            GPIO.output(COL[i],0) #pull one column pin low
            for j in range(4): #check which row pin becomes low
                if GPIO.input(ROW[j])==0: #if a key is pressed
                    PWUserChar = str(MATRIX[j][i])
                    PWUser += PWUserChar
                    while GPIO.input(ROW[j])==0: #debounce
                        sleep(0.1)
            GPIO.output(COL[i],1) #write back default value of 1
            
        
            
            LCD.lcd_display_string("Insert password:", 1) #write on line 1
            LCD.lcd_display_string(PWUser, 2) #write on line 2
            
            if len(PWUser) == 6:
                if PWUser == PWSet:    #password is correct
                    print("POGCHAMP")
                    door_state = False
                    door_check()
                    PWUser=''
                    
                elif PWUser != PWSet:  #password is incorrect
                    print("Big W")
                

#===============================================#
GPIO.setmode(GPIO.BCM) #choose BCM mode
GPIO.setwarnings(False)
GPIO.setup(26,GPIO.OUT) #set GPIO 26 as output
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
PWM=GPIO.PWM(26,50) #set 50Hz PWM output at GPIO26

LCD = I2C_LCD_driver.lcd() #instantiate an lcd object, call it LCD
sleep(0.5)
LCD.backlight(0) #turn backlight off
sleep(0.5)
LCD.backlight(1) #turn backlight on

sleep(1) #wait 1 sec
LCD.lcd_clear() #clear the display
#===============================================#

acc=adxl345.ADXL345() #instantiate
acc.load_calib_value() #load calib. values in accel_calib
acc.set_data_rate(data_rate=adxl345.DataRate.R_100) #see datasheet
acc.set_range(g_range=adxl345.Range.G_16,full_res=True) # ..
acc.measure_start()

MATRIX=[ [1,2,3],
         [4,5,6],
         [7,8,9],
         ['*',0,'#']] #layout of keys on keypad

ROW=[6,20,19,13] #row pins
COL=[12,5,16] #column pins

#set column pins as outputs, and write default value of 1 to each
for i in range(3):
    GPIO.setup(COL[i],GPIO.OUT)
    GPIO.output(COL[i],1)

#set row pins as inputs, with pull up
for j in range(4):
    GPIO.setup(ROW[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)

true = True
false = False
door_state = True

def door_check(var):
    global door_state
    if door_state:
        PWM.start(3) #3% duty cycle and 3 o'clock position
        print("bruh2")
    else:
        PWM.start(12) #13% duty cycle and 9 o'clock position
        print("bruh")



Process(target=AccDoorCheck).start()
Process(target=PWInputCheck).start()


        