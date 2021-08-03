import os
import time
os.system ("sudo pigpiod") #Launching GPIO library
time.sleep(1)
import pigpio #importing GPIO library

left_ESC=13
right_ESC=12

pi = pigpio.pi();
pi.set_servo_pulsewidth(left_ESC, 0)
pi.set_servo_pulsewidth(right_ESC, 0)
#commit


max_value = 2000 #change this if your ESC's max value is different or leave it be
min_value = 700  #change this if your ESC's min value is different or leave it be
print ("For first time launch, select calibrate")
print ("Type the exact word for the function you want")
print ("calibrate OR manual OR control OR arm OR stop")

def manual_drive(): #You will use this function to program your ESC if required
    print ("You have selected manual option so give a value between 0 and you max value")
    while True:
        inp = input()
    if inp == ("stop"):
        stop()

    elif inp == ("control"):
        control()
    elif inp == ("arm"):
        arm() 
    else:
        pi.set_servo_pulsewidth(left_ESC,inp)
        pi.set_servo_pulsewidth(right_ESC,inp)
                
def calibrate():   #This is the auto calibration procedure of a normal ESC
    pi.set_servo_pulsewidth(right_ESC, 0)
    pi.set_servo_pulsewidth(left_ESC, 0)
    print("Disconnect the battery and press Enter")
    inp = input()
    if inp == '':
        pi.set_servo_pulsewidth(left_ESC, max_value)
        pi.set_servo_pulsewidth(right_ESC, max_value)
        print("Connect the battery NOW.. you will here two beeps, then wait for a gradual falling tone then press Enter")
        inp = input()
        if inp == '':            
            pi.set_servo_pulsewidth(left_ESC, min_value)
            pi.set_servo_pulsewidth(right_ESC, min_value)
            print ("Wierd eh! Special tone")
            time.sleep(7)
            print ("Wait for it ....")
            time.sleep (5)
            print ("Im working on it, DONT WORRY JUST WAIT.....")
            pi.set_servo_pulsewidth(left_ESC, 0)
            pi.set_servo_pulsewidth(right_ESC, 0)
            time.sleep(2)
            print ("Arming ESC now...")
            pi.set_servo_pulsewidth(left_ESC, min_value)
            pi.set_servo_pulsewidth(right_ESC, min_value)
            time.sleep(1)
            print ("See.... uhhhhh")
            control()
            
def control(): 
    print ("I'm Starting the motor, I hope its calibrated and armed, if not restart by giving 'x'")
    time.sleep(1)
    left_Speed = 0  # change your speed if you want to.... it should be between 700 - 2000
    right_Speed = 0
    print ("Controls - a to decrease speed & d to increase speed OR q to decrease a lot of speed & e to increase a lot of speed")
    while True:
        pi.set_servo_pulsewidth(left_ESC, left_Speed + 1500)
        pi.set_servo_pulsewidth(right_ESC, right_Speed + 1500)
        inp = input()
        
        if inp == "s":
            left_Speed += 50    # left speed increase
            print ("speed = %d" % left_Speed)
        elif inp == "k":
            right_Speed += 50    # right speed increase
            print ("speed = %d" % right_Speed)
        elif inp == "m":
            right_Speed -= 50     # right speed decrease
            print ("speed = %d" % right_Speed)
        elif inp == "z":
            left_Speed -= 50     # left speed decrease
            print ("speed = %d" % left_Speed)
        elif inp == "stop":
            stop()
            break
        elif inp == "q":
            stop()
            break
        elif inp == "manual":
            manual_drive()
            break
        elif inp == "arm":
            arm()
            break   
        else:
            print ("WHAT DID I SAID!! Press a,q,d or e")
            
def arm():
    print ("Connect the battery and press Enter")
    inp = input()    
    if inp == '':
        pi.set_servo_pulsewidth(left_ESC, 0)
        pi.set_servo_pulsewidth(right_ESC, 0)
        time.sleep(1)
        pi.set_servo_pulsewidth(left_ESC, max_value)
        pi.set_servo_pulsewidth(right_ESC, max_value)
        time.sleep(1)
        pi.set_servo_pulsewidth(left_ESC, min_value)
        pi.set_servo_pulsewidth(right_ESC, min_value)
        time.sleep(1)
        control() 
        
def stop():
    pi.set_servo_pulsewidth(left_ESC, 0)
    pi.set_servo_pulsewidth(right_ESC, 0)
    pi.stop()

#Set motor speed between (-10, 10)
def leftMotorSpeed(Speed):
    pi.set_servo_pulsewidth(left_ESC, Speed * 50 + 1500)

def rightMotorSpeed(Speed):
    pi.set_servo_pulsewidth(left_ESC, Speed * 50 + 1500)

