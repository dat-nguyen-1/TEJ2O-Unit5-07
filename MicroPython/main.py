"""
Created by: Dat Nguyen
Created on: May 2026
This module will simulate a car's wheels.
"""

from microbit import *
from machine import time_pulse_us
import math
import utime

PCA9685_ADDR = 0x40
MODE_1 = 0x00
MODE_2 = 0x01


class HCSR04:
    def __init__(self, trigger=pin1, echo=pin2) -> None:
        self.trigger = trigger
        self.echo = echo

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


class Driver28BYJ48:
    HALF_STEP_SEQUENCE = [
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (0, 1, 0, 0),
        (0, 1, 1, 0),
        (0, 0, 1, 0),
        (0, 0, 1, 1),
        (0, 0, 0, 1),
        (1, 0, 0, 1),
    ]

    STEPS_PER_REVOLUTION = 4096

    def __init__(self) -> None:
        self.is_on = [False, False]
        self.target_time = [0, 0]
        self.step_index = [0, 0]
        self.delay = 5000
        self.init_PCA9685()

    def init_PCA9685(self) -> None:
        i2c.init()

        self.write(0x00, 0x00)
        prescale = int(25_000_000 / (50 * 4096) - 1)

        self.write(0x00, 0x10)
        self.write(0xFE, prescale)
        self.write(0x00, 0x00)
        self.write(0x00, 0xA1)

        for index in range(16):
            self.write_PWM(index, 0, 0)

    def write(self, regular: int, value: int) -> None:
        i2c.write(PCA9685_ADDR, bytes([regular, value]))

    def write_PWM(self, channel: int, on: int, off: int) -> None:
        buffer = bytes(
            [
                0x06 + 4 * channel,
                on & 0xff,
                on >> 8,
                off & 0xFF,
                off >> 8,
            ]
        )

        i2c.write(PCA9685_ADDR, buffer)

    def set_step(self, base: int, step: int) -> None:
        pattern = self.HALF_STEP_SEQUENCE[step]
        for index in range(4):
            if pattern[index]:
                self.write_PWM(base + index, 0, 4095)
            else:
                self.write_PWM(base + index, 0, 0)

    def step(self, index: int, direction: int) -> None:
        base = index * 4
        self.step_index[index] = (self.step_index[index] + direction) % len(
            self.HALF_STEP_SEQUENCE
        )

        self.set_step(base, self.step_index[index])

        utime.sleep_us(self.delay)

    def step_all(self, directions: list[int]) -> None:
        for index, direction in enumerate(directions):
            self.step(index, -direction)

    def stop(self, index: int) -> None:
        base = index * 4
        for index in range(4):
            self.write_PWM(base + index, 0, 0)

    def stop_all(self) -> None:
        for index in range(16):
            self.write_PWM(index, 0, 0)

    def set_delay(self, delay_us: int) -> None:
        self.delay = delay_us

    def move_cm(self, distance: int, wheel_diameter: int = 10) -> None:
        circumference = math.pi * wheel_diameter
        revolutions = distance / circumference
        steps = abs(int(revolutions * self.STEPS_PER_REVOLUTION))

        for _ in range(steps):
            if distance > 0:
                direction = 1
            else:
                direction = -1

            self.step_all([direction, direction])

    def turn_degrees(self, degrees: int, wheel_diameter: int, track: int) -> None:
        track_circumference = math.pi * track
        wheel_circumfrence = math.pi * wheel_diameter

        rotations = degrees * track_circumference / wheel_circumfrence / 360
        steps = abs(int(rotations * self.STEPS_PER_REVOLUTION))

        for _ in range(steps):
            if degrees > 0:
                direction = 1
            else:
                direction = -1

            self.step_all([direction, -direction])


# constants
TRACK = 20
WHEEL_DIAMETER = 6

# initialize hardware instances
STEPPER_DRIVER = Driver28BYJ48()
SONAR = HCSR04(trigger=pin1, echo=pin2)

while True:
    # get distance
    distance_cm = SONAR.get_distance_cm()
    print(distance_cm)

    if -1 < distance_cm <= 10:
        # turn wheels backwards 10 cm
        STEPPER_DRIVER.stop_all()
        STEPPER_DRIVER.move_cm(-10, WHEEL_DIAMETER)

        # rotate 90 degrees in place
        STEPPER_DRIVER.turn_degrees(90, WHEEL_DIAMETER, TRACK)
    else:
        # move forward
        STEPPER_DRIVER.step_all([1, 1])
