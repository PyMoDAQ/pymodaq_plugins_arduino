from typing import Optional


from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, main,
                                                          DataActuatorType, Q_,
                                                          DataActuator)
from pymodaq_utils.utils import ThreadCommand
from pymodaq_gui.parameter import Parameter


from pymodaq_plugins_arduino.hardware.arduino_telemetrix import Arduino
from pymodaq_plugins_arduino.utils import Config

config = Config()


class DAQ_Move_Servo(DAQ_Move_base):
    """ Instrument plugin class for an actuator.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    """
    _axis_names = {'Servo': config('servo', 'pin')}
    _controller_units = {'Servo': '°'}
    _epsilons = {'Servo': 1}

    data_actuator_type = DataActuatorType['DataActuator']

    params = [
                 {'title': 'Ports:', 'name': 'com_port', 'type': 'list',
                  'value': config('com_port'), 'limits': Arduino.COM_PORTS}
             ] + comon_parameters_fun(axis_names=_axis_names)

    def ini_attributes(self):
        self.controller: Optional[Arduino] = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        pos = DataActuator(data=self.controller.get_output_pin_value(self.axis_value),
                           units=self.axis_unit)
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
        self.controller.set_pin_mode_servo(config('servo', 'pin'))

        self.emit_status(ThreadCommand('update_ui', attribute='set_abs_value_red',
                                       args=[Q_(config('servo', 'pos_1'),
                                                self.axis_unit)]))
        self.emit_status(ThreadCommand('update_ui', attribute='set_abs_value_green',
                                       args=[Q_(config('servo', 'pos_2'),
                                                self.axis_unit)]))
        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        self.controller.servo_move_degree(self.axis_value,
                                          value.units_as(self.axis_unit).value())

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
        self.controller.servo_move_degree(self.axis_value,
                                          self.target_value.units_as(self.axis_unit).value())

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.servo_move_degree(self.axis_value, 0)

    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""
      pass


if __name__ == '__main__':
    main(__file__)
