import RPi.GPIO as GPIO #import RPi.GPIO module
from time import sleep
import adxl345
import I2C_LCD_driver
from multiprocessing import Process
import sys

#=================Global-Variable================#
PWSet = '1'
door_state = True
#===============================================#

GPIO.setmode(GPIO.BCM) #choose BCM mode
GPIO.setwarnings(False)
GPIO.setup(26,GPIO.OUT) #set GPIO 26 as output
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
#===============================================#

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
#===============================================#

def DoorLock(state):
    if state:
        PWM.start(3) #3% duty cycle
        print("Door Locked! Duty Cycle: 3") #3 o'clock position
        sleep(1) #allow time for movement
        
      
    else:
        PWM.start(12) #3% duty cycle
        print("Door Unlocked! Duty Cycle: 12") #3 o'clock position
        sleep(1) #allow time for movement



def AccDoorCheck():
    while True:
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
    DoorLock(door_state)
    
    while 1:
        LCD.lcd_display_string("Insert password:", 1) #write on line 1
        
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
        
        if len(PWUser) == 1:
            if PWUser == PWSet:    #password is correct
                print("Door is unlocked! Password is Correct!")
                PWUser=''
                LCD.lcd_clear() #clear the display
                LCD.lcd_display_string("Door Unlocked!", 1)
                LCD.lcd_display_string("Welcome!", 2)
                door_state = False
                DoorLock(door_state)
                    
                sleep(2)
                LCD.lcd_clear() #clear the display
                LCD.lcd_display_string("Door Locked!", 1)
                LCD.lcd_display_string("Goodbye!", 2)
                door_state = True
                DoorLock(door_state)
                    
                    
                    
                LCD.lcd_clear() #clear the display
    
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
                    
                    

Process(target=AccDoorCheck).start()
Process(target=PWInputCheck).start()
