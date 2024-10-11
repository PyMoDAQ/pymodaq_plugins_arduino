from typing import Optional


from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, main,
                                                          DataActuatorType,
                                                          DataActuator)
from pymodaq_utils.utils import ThreadCommand
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_arduino.hardware.arduino_telemetrix import Arduino
from pymodaq_plugins_arduino.utils import Config

config = Config()


class DAQ_Move_LED(DAQ_Move_base):
    """ Instrument plugin class for an actuator.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    """
    _controller_units = ''
    is_multiaxes = True
    _axis_names = {'Red': config('LED', 'pins', 'red_pin'),
                   'Green': config('LED', 'pins', 'green_pin'),
                   'Blue': config('LED', 'pins', 'blue_pin'),
                   }
    _epsilon = 0.01
    data_actuator_type = DataActuatorType['DataActuator']

    params = [
                 {'title': 'Ports:', 'name': 'com_port', 'type': 'list',
                  'value': config('com_port'), 'limits': Arduino.COM_PORTS}

                ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: Optional[Arduino] = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        pos = DataActuator(data=self.controller.get_output_pin_value(self.axis_value))  # when writing your own plugin replace this line
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
        ## TODO for your custom plugin
        pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        self.controller = self.ini_stage_init(
            old_controller=controller,
            new_controller=None)
        if self.is_master:
            self.controller = Arduino(
                com_port=self.settings['com_port']
                                              )
            self.set_pins()

        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def set_pins(self):
        for pin in config('LED', 'pins').values():
            self.controller.set_pin_mode_analog_output(pin)

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        self.controller.analog_write_and_memorize(self.axis_value,
                                                  int(value.value()))

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        # value is set in percent
        self.controller.analog_write_and_memorize(self.axis_value,
                                                  int(self.target_value.value()))

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.analog_write_and_memorize(self.axis_value, 0)

    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""
      pass


if __name__ == '__main__':
    main(__file__)
