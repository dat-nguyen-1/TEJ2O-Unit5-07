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


PCA9685_ADDR = 0x40
MODE_1 = 0x00
MODE_2 = 0x01


def init_PCA9685():
    i2c.init(sda=pin20, scl=pin19)
    set_frequency(50)

    for index in range(16):
        set_PWM(index, 0, 0)

    i2c.write(PCA9685_ADDR, 0x00, 0x00)


def set_frequency(frequency: int):
    pre_scale_value = 25_000_000 / (frequency * 4096)
    pre_scale_value -= 1

    old_mode = i2c.read(PCA9685_ADDR, 0x00)
    new_mode = (old_mode & 0x7f) | 0x10

    i2c.write(PCA9685_ADDR, 0x00, new_mode)
    i2c.write(PCA9685_ADDR, 0xFE, pre_scale_value)
    i2c.write(PCA9685_ADDR, 0x00, old_mode)
    utime.sleep_us(5000)
    i2c.write(PCA9685_ADDR, 0x00, old_mode | 0xa1)


def set_PWM(channel: int, on: int, off: int):
    buffer = bytes([
        0x06 + 4 * channel,
        on & 0xff,
        (on >> 8) & 0xFF,
        off & 0xFF,
        (off >> 8) & 0xFF,
    ])

    i2c.write(PCA9685_ADDR, buffer)


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

    def __init__(self, index: int) -> None:
        self.step_index = 0

    def set_stepper(self, index: int, direction: int):
        if index == 1:
            if direction == 1:
                set_PWM(0, 2047, 4095)
                set_PWM(2, 1, 2047)
                set_PWM(1, 1023, 3071)
                set_PWM(3, 3071, 1023)
            

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
