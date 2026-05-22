"""
Created by: Dat Nguyen
Created on: May 2026
This module will simulate a car's wheels.
"""

from microbit import *
from machine import time_pulse_us
import math
import utime

# turn off display for more pins
display.off()


class HCSR04:
    def __init__(self, trigger=pin1, echo=pin2) -> None:
        self.trigger = trigger
        self.echo = echo

        # initialize pins
        self.trigger.write_digital(0)
        self.echo.read_digital()

    def get_distance_cm(self) -> float:
        self.trigger.write_digital(0)
        utime.sleep_us(2)
        self.trigger.write_digital(1)
        utime.sleep_us(10)
        self.trigger.write_digital(0)

        time_us = time_pulse_us(self.echo, 1)

        if time_us <= 0:
            return -1.0

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

    def __init__(self, in1=pin0, in2=pin1, in3=pin2, in4=pin8) -> None:
        self.pins = [in1, in2, in3, in4]
        self.step_index = 0

    def step(self, direction: int, delay_ms: int = 1) -> None:
        current_step = self.HALF_STEP_SEQUENCE[self.step_index]
        for index in range(4):
            self.pins[index].write_digital(current_step[index])

        self.step_index = (self.step_index + direction) % 8
        sleep(delay_ms)

    def turn_degrees(self, degrees: int, delay_ms: int = 1) -> None:
        if degrees > 0:
            direction = 1
        else:
            direction = -1

        abs_degrees = abs(degrees)
        steps = int(abs_degrees / 360 * self.HALF_STEPS_PER_REV)

        for _ in range(steps):
            self.step(direction, delay_ms)

    def turn_cm(
        self, distance: int, wheel_diameter: int = 1, delay_ms: int = 1
    ) -> None:

        circumference = math.pi * wheel_diameter
        degrees = int((distance * 360) / circumference)

        self.turn_degrees(degrees, delay_ms)


class StepperCar:
    def __init__(
        self,
        stepper_left: Stepper28BYJ48,
        stepper_right: Stepper28BYJ48,
        track: float,
        wheel_diameter: float,
    ) -> None:

        self.stepper_left = stepper_left
        self.stepper_right = stepper_right
        self.track = track
        self.wheel_diameter = wheel_diameter

    def step(delay_ms: int = 1) -> None:
        self.stepper_left.step(1)
        self.stepper_right.step(-1)

    def move_cm(cm, delay_ms: int = 1) -> None:
        self.stepper_left.turn_cm(cm)
        self.stepper_right.turn_cm(-cm)

    def turn_degrees(degrees, delay_ms: int = 1) -> None:
        target_wheel_degrees = int((TRACK * 90) / WHEEL_DIAMETER)

        self.stepper_left.turn_degrees(-target_wheel_degrees)
        self.stepper_right.turn_degrees(-target_wheel_degrees)


# constants
TRACK = 100.0
WHEEL_DIAMETER = 20.0

# initialize hardware instances
STEPPER_1 = Stepper28BYJ48(pin0, pin1, pin2, pin3)
STEPPER_2 = Stepper28BYJ48(pin12, pin13, pin14, pin15)
SONAR = HCSR04(trigger=pin9, echo=pin10)
CAR = StepperCar(STEPPER_1, STEPPER_2, TRACK, WHEEL_DIAMETER)

while True:
    # get distance
    distance_cm = SONAR.get_distance_cm()

    if distance_cm <= 10:
        # turn wheels backwards 10 cm
        CAR.move_cm(-10)

        # rotate 90 degrees in place
        CAR.turn_degrees(90)
    else:
        # move forward
        CAR.step()
