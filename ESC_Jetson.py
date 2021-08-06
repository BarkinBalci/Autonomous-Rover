import time
from adafruit_servokit import ServoKit

kit = ServoKit(channels=8)

#Motors
leftMotor = 0
rightMotor = 1

#Pulse Width Range
kit.servo[leftMotor].set_pulse_width_range(1000, 2000)
kit.servo[rightMotor].set_pulse_width_range(1000, 2000)


def control():
    print("Starting the motors, first it should be calibrated and armed, if not restart the program using 'x'")
    time.sleep(1)
    leftSpeed = 0
    rightSpeed = 0
    # change your speed if you want to.... it should be between 700 - 2000

    print("Controls - Left s+ z- / Right k+ m-")
    print("Brake - v")
    while True:

        inp = input()

        if inp == "s":
            leftSpeed += 0.05  # decrementing the speed a lot
            print("Speed = %" + str(left_speed * 100))
        if inp == "z":
            leftSpeed -= 0.05  # incrementing the speed a lot
            print("speed = %" + str(left_speed * 100))
        if inp == "k":
            rightSpeed += 0.05 # incrementing the speed
            print("speed = %" + str(right_speed * 100))
        if inp == "m":
            rightSpeed -= 0.05  # decrementing the speed
            print("speed = %" + str(right_speed * 100))
        if inp == "v":
            left_speed = 0  # decrementing the speed
            right_speed = 0  # decrementing the speed
            print("speed = %" + str(left_speed * 100))
            print("speed = %" + str(right_speed * 100))
        kit.continuous_servo[leftMotor].throttle = (leftSpeed)
        kit.continuous_servo[rightMotor].throttle = (rightSpeed)

def leftMotorSpeed(Speed):
    kit.continuous_servo[leftMotor].throttle = (Speed)

def rightMotorSpeed(Speed):
    kit.continuous_servo[rightMotor].throttle = (Speed)
