#!/usr/bin/env python

# Copyright (c) 2019-2020, NVIDIA CORPORATION. All rights reserved.
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import RPi.GPIO as GPIO
import time

left_output_pins = {
    'JETSON_NANO': 32,
}

right_output_pins = {
    'JETSON_NANO': 33,
}
left_output_pin = left_output_pins.get(GPIO.model, None)
if left_output_pin is None:
    raise Exception('PWM not supported on this board')
right_output_pin = right_output_pins.get(GPIO.model, None)
if right_output_pin is None:
    raise Exception('PWM not supported on this board')



GPIO.setmode(GPIO.BOARD)
# set pin as an output pin with optional initial state of HIGH
GPIO.setup(left_output_pin, GPIO.OUT)
leftMotor = GPIO.PWM(left_output_pin, 50)
rightMotor = GPIO.PWM(right_output_pin, 50)
leftSpeed = 50
leftIncrease = 5
rightSpeed = 50
rightIncrease = 5
maxSpeed = 100
lowestSpeed = 0
leftMotor.start(leftSpeed)
rightMotor.start(leftSpeed)


print("PWM running. Press CTRL+C to exit.")
def main():
    try:
        while True:
            inp = input()
            if inp == "s" and leftSpeed < maxSpeed:
                leftSpeed += leftIncrease
            elif inp == "z" and leftSpeed > lowestSpeed:
                leftSpeed -= leftIncrease
            elif inp == "k" and rightSpeed < maxSpeed:
                rightSpeed += rightIncrease
            elif inp == "m" and rightSpeed > lowestSpeed:
                rightSpeed -= rightIncrease
            elif inp == "forward":
                leftSpeed = 100
                rightSpeed = 100
            elif inp == "backward":
                leftSpeed = 0
                rightSpeed = 0
            elif inp == "v":
                leftSpeed = 50
                rightSpeed = 50

            leftMotor.ChangeDutyCycle(leftSpeed)
            rightMotor.ChangeDutyCycle(rightSpeed)
            print("Left Motor Speed: " + str(leftSpeed))
            print("Right Motor Speed: " + str(rightSpeed))
    finally:
        leftMotor.stop()
        rightMotor.stop()
        GPIO.cleanup()

def leftMotorSpeed(Speed):
    leftMotor.ChangeDutyCycle(Speed)
    print("Left Motor Speed: " + str(leftSpeed))
def rightMotorSpeed(Speed):
    rightMotor.ChangeDutyCycle(Speed)
    print("Right Motor Speed: " + str(rightSpeed))

def disarm():
    leftMotor.stop()
    rightMotor.stop()
    GPIO.cleanup()