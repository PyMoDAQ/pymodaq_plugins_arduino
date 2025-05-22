import sys
import time
from telemetrix import telemetrix
from threading import Event


class StepperMotorController:
    def __init__(self, pulse_pin, direction_pin, enable_pin=7):
        self.pulse_pin = pulse_pin
        self.direction_pin = direction_pin
        self.enable_pin = enable_pin
        self.board = telemetrix.Telemetrix()
        self.motor = self.board.set_pin_mode_stepper(interface=1, pin1=self.pulse_pin, pin2=self.direction_pin)
        self.completion_event = Event()

        # Initialize the enable pin
        self.board.set_pin_mode_digital_output(self.enable_pin)
        self.board.digital_write(self.enable_pin, 1)  # Disbale the motor driver

    def the_callback(self, data):
        self.completion_event.set()  # Signal that the motion is complete

    def move_to_position(self, position, max_speed=400, acceleration=800):
        # Set motor parameters
        self.board.stepper_set_current_position(self.motor, 0)
        self.board.stepper_set_max_speed(self.motor, max_speed)
        self.board.stepper_set_acceleration(self.motor, acceleration)

        # Set the target position
        self.board.stepper_move_to(self.motor, position)

        # Run the motor and wait for completion
        print(f'Starting motor to move to position {position}...')
        self.completion_event.clear()
        self.board.digital_write(self.enable_pin, 0)  # Enable the motor driver
        self.board.stepper_run(self.motor, completion_callback=self.the_callback)
        self.completion_event.wait()  # Block until the motion is complete
        self.board.digital_write(self.enable_pin, 1)

    def shutdown(self):
        self.board.shutdown()
          # Disable the motor driver


if __name__ == "__main__":
    try:
        # Create an instance of the StepperMotorController
        stepper = StepperMotorController(pulse_pin=8, direction_pin=9)

        # Move to the first position
        stepper.move_to_position(2000)

        # Move to the opposite position
        print('Running motor in opposite direction...')
        stepper.move_to_position(-2000)

        # Shutdown the board
        stepper.shutdown()

    except KeyboardInterrupt:
        stepper.shutdown()
        sys.exit(0)