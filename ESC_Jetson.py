import os  # importing os library
import time  # importing time

os.system("sudo pigpiod")  # Launching GPIO library
time.sleep(1)  # don't remove this, else you will get an error
import pigpio  # importing GPIO library

lMotor = 4  # ESC connections with the GPIO pins; note its the BROADCOM number, not the GPIO pin number!
rMotor = 17

pi = pigpio.pi();
pi.set_servo_pulsewidth(lMotor, 0)
pi.set_servo_pulsewidth(rMotor, 0)


max_value = 2000  # change this if your ESC's max value is different or leave it
min_value = 700  # change this if your ESC's min value is different or leave it
print("For first time launch, select calibrate")
print("Type the exact word for the function you want")
print("calibrate OR manual OR control OR arm OR stop")


def manual_drive():  # You will use this function to program your ESC if required
    print("Manual mode selected: give a value between 0 and 2500")
    while True:
        inp = input()
        if inp == "stop":
            stop()
            break
        elif inp == "control":
            control()
            break
        elif inp == "arm":
            arm()
            break
        else:
            pi.set_servo_pulsewidth(lMotor, inp)
            pi.set_servo_pulsewidth(rMotor, inp)

def calibrate():  # This is the auto calibration procedure of a normal ESC
    pi.set_servo_pulsewidth(lMotor, 0)
    pi.set_servo_pulsewidth(rMotor, 0)
    print("Disconnect the battery and press Enter")
    inp = input()
    if inp == '':
        pi.set_servo_pulsewidth(lMotor, max_value)
        pi.set_servo_pulsewidth(rMotor, max_value)
        print(
            "Connect the battery NOW.. you will here two beeps, then wait for a gradual falling tone then press Enter")
        inp = input()
        if inp == '':
            pi.set_servo_pulsewidth(lMotor, min_value)
            pi.set_servo_pulsewidth(rMotor, min_value)
            print("Wait...")
            time.sleep(7)
            print("Wait for it ....")
            time.sleep(5)
            print("WAIT...")
            pi.set_servo_pulsewidth(lMotor, 0)
            pi.set_servo_pulsewidth(rMotor, 0)
            time.sleep(2)
            print("Arming ESC now...")
            pi.set_servo_pulsewidth(lMotor, min_value)
            pi.set_servo_pulsewidth(rMotor, min_value)
            time.sleep(1)
            print("Here it goes!")
            control()  # You can change this to any other function you want


def control():
    print("Starting the motors, first it should be calibrated and armed, if not restart the program using 'x'")
    time.sleep(1)
    left_speed = 0
    right_speed = 0
    # change your speed if you want to.... it should be between 700 - 2000

    print("Controls - Left s+ z- / Right k+ m-")
    print("Brake - v")
    while True:
        pi.set_servo_pulsewidth(lMotor, left_speed + 1500)
        pi.set_servo_pulsewidth(rMotor, right_speed + 1500)
        inp = input()

        if inp == "s":
            left_speed += 50  # decrementing the speed a lot
            print("speed = %d" % (left_speed,))
        elif inp == "z":
            left_speed -= 50  # incrementing the speed a lot
            print("speed = %d" % (left_speed,))
        elif inp == "k":
            right_speed += 50 # incrementing the speed
            print("speed = %d" % (right_speed,))
        elif inp == "m":
            right_speed -= 50  # decrementing the speed
            print("speed = %d" % (right_speed,))
        elif inp == "v":
            left_speed = 0  # decrementing the speed
            right_speed = 0  # decrementing the speed
            print("speed = %d" % (left_speed,))
            print("speed = %d" % (right_speed,))
        elif inp == "stop":
            stop()  # stopping everything
            break
        elif inp == "manual":
            manual_drive()
            break
        elif inp == "arm":
            arm()
            break
        else:
            print("Press a,q,d or e for controls")


def arm():  # This is the arming procedure of an ESC
    print("Connect the battery and press Enter")
    inp = input()
    if inp == '':
        pi.set_servo_pulsewidth(lMotor, 0)
        pi.set_servo_pulsewidth(rMotor, 0)
        time.sleep(1)
        pi.set_servo_pulsewidth(lMotor, max_value)
        pi.set_servo_pulsewidth(rMotor, max_value)
        time.sleep(1)
        pi.set_servo_pulsewidth(lMotor, min_value)
        pi.set_servo_pulsewidth(rMotor, min_value)
        time.sleep(1)
        control()


def stop():  # This will stop every action your Pi is performing for ESC ofcourse.
    pi.set_servo_pulsewidth(lMotor, 0)
    pi.set_servo_pulsewidth(rMotor, 0)
    pi.stop()

def leftMotorSpeed(Speed):
    pi.set_servo_pulsewidth(lMotor, Speed * 50 + 1500)

def rightMotorSpeed(Speed):
    pi.set_servo_pulsewidth(lMotor, Speed * 50 + 1500)


inp = input()
if inp == "manual":
    manual_drive()
elif inp == "calibrate":
    calibrate()
elif inp == "arm":
    arm()
elif inp == "control":
    control()
elif inp == "stop":
    stop()
else:
    print("Something is not right, jsut check and restart the program")