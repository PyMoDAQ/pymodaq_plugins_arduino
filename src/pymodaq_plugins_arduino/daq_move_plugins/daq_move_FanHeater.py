from typing import Optional

from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, main,
                                                          DataActuatorType, DataActuator)
from pymodaq_utils.utils import ThreadCommand
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.utils import Config

config = Config()


class DAQ_Move_FanHeater(DAQ_Move_base):
    """Instrument plugin class for the heater and fan actuators.

    This object inherits all functionalities to communicate with PyMoDAQ's DAQ_Move module through
    inheritance via DAQ_Move_base.  It makes a bridge between the DAQ_Move module and the Python
    wrapper of a particular instrument.

    Both actuators are driven by a XY-MOS PWM board connected to an ESP32 over WiFi using the
    Telemetrix AIO protocol.  The PWM duty cycle ranges from 0 to 255 (8-bit resolution).

        Heater
        Fan    

    Attributes:
    -----------
    controller: object
        The particular object that allows communication with the hardware, in general a Python
        wrapper around the hardware library.
    """

    _controller_units = '' # raw PWM level (0-255) unit depends on wired device
    is_multiaxes = True
    _axis_names = {
        'Heater': config('esp32', 'pins', 'heater_pin'),
        'Fan':    config('esp32', 'pins', 'fan_pin'),
    }
    _epsilon = 0.1
    data_actuator_type = DataActuatorType['DataActuator']

    params = [
        {'title': 'IP Address:', 'name': 'ip_address', 'type': 'str',
         'value': config('esp32', 'ip_address')},
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: Optional[ArduinoWifi] = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(data=self.controller.get_output_pin_value(self.axis_value), units=self.axis_unit)
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.set_pins_output_to(0)
            self.controller.shutdown()

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:
            self.controller = ArduinoWifi(
                ip_address=self.settings['ip_address']
            )
            self.set_pins()
        else:
            self.controller = controller

        info = "Heater and Fan ready"
        initialized = True
        return info, initialized

    def set_pins(self):
        """Configure every axis pin as a PWM output and reset it to 0."""
        for pin in self._axis_names.values():
            self.controller.set_pin_mode_analog_output(pin)
            self.controller.analog_write_and_memorize(pin, 0)

    def move_abs(self, value: DataActuator):
        """Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """
        value = self.check_bound(value)                  # apply user-defined bounds
        self.target_value = value
        value = self.set_position_with_scaling(value)    # apply scaling if the user specified one

        self.controller.analog_write_and_memorize(self.axis_value, int(value.value(self.axis_unit)))

    def move_rel(self, value: DataActuator):
        """Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        # PWM value is set in duty-cycle counts (0–255)
        self.controller.analog_write_and_memorize(self.axis_value, int(self.target_value.value(self.axis_unit)))
        
    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.analog_write_and_memorize(self.axis_value, 0)

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        pass


if __name__ == '__main__':
    main(__file__)
