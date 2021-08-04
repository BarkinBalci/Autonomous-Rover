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

output_pins = {
    'JETSON_XAVIER': 18,
    'JETSON_NANO': 33,
    'JETSON_NX': 33,
    'CLARA_AGX_XAVIER': 18,
    'JETSON_TX2_NX': 32,
}
output_pin = output_pins.get(GPIO.model, None)
if output_pin is None:
    raise Exception('PWM not supported on this board')


def main():
    # Pin Setup:
    # Board pin-numbering scheme
    GPIO.setmode(GPIO.BOARD)
    # set pin as an output pin with optional initial state of HIGH
    GPIO.setup(output_pin, GPIO.OUT, initial=GPIO.HIGH)
    leftMotor = GPIO.PWM(output_pin, 50)
    rightMotor = GPIO.PWM(output_pin, 79)
    val = 1500
    leftSpeed = 0
    rightSpeed = 0
    leftMotor.start(val)
    rightMotor.start(val)

    print("PWM running. Left Motor s+ z- / Right Motor k+ m- / Stop v")
    try:
        while True:
            leftMotor.ChangeDutyCycle(val + leftSpeed)
            rightMotor.ChangeDutyCycle(val + rightSpeed)
            inp = input()
            if inp == "s":
                leftSpeed += 50  # decrementing the speed a lot
                print("speed = %d" % (leftSpeed,))
            elif inp == "z":
                leftSpeed -= 50  # incrementing the speed a lot
                print("speed = %d" % (leftSpeed,))
            elif inp == "k":
                rightSpeed += 50  # incrementing the speed
                print("speed = %d" % (rightSpeed,))
            elif inp == "m":
                rightSpeed -= 50  # decrementing the speed
                print("speed = %d" % (rightSpeed,))
            elif inp == "v":
                leftSpeed = 0  # decrementing the speed
                rightSpeed = 0  # decrementing the speed
                print("speed = %d" % (leftSpeed,))
                print("speed = %d" % (rightSpeed,))
    finally:
        leftMotor.stop()
        rightMotor.stop()
        GPIO.cleanup()

if __name__ == '__main__':
    main()