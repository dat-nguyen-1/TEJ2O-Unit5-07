"""
Created by: Dat Nguyen
Created on: May 2026
This module will simulate a car's wheels.
"""

from microbit import *
from machine import time_pulse_us
import math


# turn off display for more pins
display.off()

class HCSR04:
    def __init__(self, trigger=pin1, echo=pin2):
        self.trigger = trigger
        self.echo = echo

        # initialize pins
        self.trigger.write_digital(0)
        self.echo.read_digital()
        
    def get_distance_cm(self):
        self.trigger.write_digital(1)
        self.trigger.write_digital(0)
        
        time_us = time_pulse_us(self.echo, 1)
        distance_cm = time_us * 0.5 * 0.0343

        return distance_cm


class Stepper28BYJ48:
    HALF_STEPS_PER_REV = 4096
    HALF_STEP_SEQUENCE = [
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
        [1, 0, 0, 0],
    ]

    def __init__(self, in1=pin0, in2=pin1, in3=pin2, in4=pin8):
        self.pins = [in1, in2, in3, in4]
        self.step_index = 0

    def step(self, direction):
        current_step = self.HALF_STEP_SEQUENCE[self.step_index]
        for index in range(4):
            self.pins[index].write_digital(current_step[index])
        
        self.step_index = (self.step_index + direction) % 8
    
    def turn_degrees(self, degrees, delay_ms=1):
        if degrees > 0:
            direction = 1
        else:
            direction = -1

        abs_degrees = abs(degrees)
        steps = int(abs_degrees / 360 * self.HALF_STEPS_PER_REV)
        
        for _ in range(steps):
            self.step(direction)
            sleep(delay_ms)

    def turn_cm(self, distance, delay_ms=1, wheel_diameter=1):
        circumference = math.pi * wheel_diameter
        degrees = (distance * 360) / circumference
        
        self.turn_degrees(degrees, delay_ms)


TRACK = 100
WHEEL_DIAMETER = 20

STEPPER_1 = Stepper28BYJ48(pin0, pin1, pin2, pin3)
STEPPER_2 = Stepper28BYJ48(pin4, pin6, pin7, pin8)
SONAR = HCSR04(trigger=pin9, echo=pin10)

while True:
    distance_cm = SONAR.get_distance_cm()

    if distance_cm <= 10:
        STEPPER_1.turn_cm(-10)
        STEPPER_2.turn_cm(-10)

        wheel_degrees = (TRACK * 90) / WHEEL_DIAMETER
        STEPPER_1.turn_degrees(wheel_degrees)
        STEPPER_1.turn_degrees(-wheel_degrees)
        
    else:
        STEPPER_1.step(1)
        STEPPER_2.step(1)
    
