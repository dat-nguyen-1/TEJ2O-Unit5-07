/* Copyright (c) 2020 MTHS All rights reserved
 *
 * Created by: Dat Nguyen
 * Created on: May 2026
 * This program will simulate a car's wheels.
*/

// constants
const WHEEL_DIAMETER: number = 60
const TRACK: number = 100

// intiialize variables
let distance: number = 0

robotbit.MotorStopAll()

input.onButtonPressed(Button.A, function() {
    // forever loop
    while (true) {
        // get distance
        distance = sonar.ping(
            DigitalPin.P1, 
            DigitalPin.P2, 
            PingUnit.Centimeters
        )

        // distance within 10 cm
        if (distance <= 10 && distance > 0) {
            // move back 10 cm and turn 90 degrees
            robotbit.StpCarMove(-10, WHEEL_DIAMETER)
            robotbit.StpCarTurn(90, WHEEL_DIAMETER, TRACK)
        } else {
            // turn motors forward
            robotbit.StpCarMove(1, WHEEL_DIAMETER)
        }
    }
})
