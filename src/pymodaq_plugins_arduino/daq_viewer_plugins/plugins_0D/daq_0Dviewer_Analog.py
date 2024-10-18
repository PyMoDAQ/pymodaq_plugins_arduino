import numpy as np
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from typing import Optional

from pymodaq_plugins_arduino.hardware.arduino_telemetrix import Arduino
from pymodaq_plugins_arduino.utils import Config


config = Config()
class DAQ_0DViewer_Analog(DAQ_Viewer_base):
    """ Instrument plugin class for a OD viewer.

    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    This plugins is intended to work with Arduino UNO type board. It should be working for others but haven't been
    tested yet (10/2024). This plugin use the Telemetrix implementation developed here:
    (https://mryslab.github.io/telemetrix/).
    It has been tested with an Arduino Uno with PyMoDAQ Version was 4.4.2 on Windows 10 Pro (Ver 22h2)

    This plugin needs to upload Telemetrix4Arduino to your Arduino-Core board (see Telemetrix installation)

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

   """
    _controller_units=''
    params = comon_parameters + [{'title': 'Ports:', 'name': 'com_port', 'type': 'list',
                  'value': config('com_port'), 'limits': Arduino.COM_PORTS},
        {'title': 'Separated viewers', 'name': 'sep_viewers', 'type': 'bool', 'value': False},
        {'name':'AI0', 'type':'group','children':[
            {'title': 'Activate', 'name': 'ch', 'type': 'led_push', 'value':False, 'label':'On/Off',
             'tip':'click to change status, Green: On, Red: Off'},
            {'title': 'Units:', 'name': 'ai_ch0_units', 'type': 'list',
             'limits': ['Integer bit','Volts','pH Units', 'Absorbance', 'Transmitance'],
             'value': 'Volts'},
        ]},{'name':'AI1', 'type':'group','children':[
            {'title': 'Activate', 'name': 'ch', 'type': 'led_push', 'value':False, 'label':'On/Off',
             'tip':'click to change status, Green: On, Red: Off'},
            {'title': 'Units:', 'name': 'ai_ch1_units', 'type': 'list',
             'limits': ['Integer bit','Volts','pH Units', 'Absorbance', 'Transmitance'],
             'value': 'Volts'},
        ]},{'name':'AI2', 'type':'group','children':[
            {'title': 'Activate', 'name': 'ch', 'type': 'led_push', 'value':False, 'label':'On/Off',
             'tip':'click to change status, Green: On, Red: Off'},
            {'title': 'Units:', 'name': 'ai_ch2_units', 'type': 'list',
             'limits': ['Integer bit','Volts','pH Units', 'Absorbance', 'Transmitance'],
             'value': 'Volts'},
        ]},{'name':'AI3', 'type':'group','children':[
            {'title': 'Activate', 'name': 'ch', 'type': 'led_push', 'value':False, 'label':'On/Off',
             'tip':'click to change status, Green: On, Red: Off'},
            {'title': 'Units:', 'name': 'ai_ch3_units', 'type': 'list',
             'limits': ['Integer bit','Volts','pH Units', 'Absorbance', 'Transmitance'],
             'value': 'Volts'},
        ]},{'name':'AI4', 'type':'group','children':[
            {'title': 'Activate', 'name': 'ch', 'type': 'led_push', 'value':False, 'label':'On/Off',
             'tip':'click to change status, Green: On, Red: Off'},
            {'title': 'Units:', 'name': 'ai_ch4_units', 'type': 'list',
             'limits': ['Integer bit','Volts','pH Units', 'Absorbance', 'Transmitance'],
             'value': 'Volts'},
        ]},{'name':'AI5', 'type':'group','children':[
            {'title': 'Activate', 'name': 'ch', 'type': 'led_push', 'value':False, 'label':'On/Off',
             'tip':'click to change status, Green: On, Red: Off'},
            {'title': 'Units:', 'name': 'ai_ch5_units', 'type': 'list',
             'limits': ['Integer bit','Volts','pH Units', 'Absorbance', 'Transmitance'],
             'value': 'Volts'},
        ]}

    ]

    def ini_attributes(self):
        self.controller: Optional[Arduino] = None
        pass

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "ai0":
            if param.value():
                self.controller.set_analog_input(0)
            else:
                self.controller.disable_analog_reporting(0)
        if param.name() == "ai1":
            if param.value():
                self.controller.set_analog_input(1)
            else:
                self.controller.disable_analog_reporting(1)
        if param.name() == "ai2":
            if param.value():
                self.controller.set_analog_input(2)
            else:
                self.controller.disable_analog_reporting(2)
        if param.name() == "ai3":
            if param.value():
                self.controller.set_analog_input(3)
            else:
                self.controller.disable_analog_reporting(3)
        if param.name() == "ai4":
            if param.value():
                self.controller.set_analog_input(4)
            else:
                self.controller.disable_analog_reporting(4)
        if param.name() == "ai5":
            if param.value():
                self.controller.set_analog_input(5)
            else:
                self.controller.disable_analog_reporting(5)


    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        self.ini_detector_init(slave_controller=controller)

        if self.is_master:
            self.controller = Arduino(com_port=self.settings['com_port'])  # instantiate you driver with whatever arguments are needed

        info = "Analog ready"
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.shutdown()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        data_tot=[]
        channel_available=[]

        for param in self.settings.children():
            if 'AI' in param.name():
                if param['ch']:
                    channel_available.append(int(param.name()[2:3]))
                    self.controller.set_analog_input(int(param.name()[2:3]))
                    data_tot.append(np.array([self.controller.analog_pin_values_input[int(param.name()[2:3])]]))

        if self.settings.child('sep_viewers').value():
            dat = DataToExport('Analog0D',
                               data=[DataFromPlugins(name=f'AI{channel_available[ind]}', data=[data],
                                                     dim='Data0D',
                                                     labels=[f'AI{channel_available[ind]} data '])
                                                             for ind, data in enumerate(data_tot)])
            self.dte_signal.emit(dat)
        else:
            self.dte_signal.emit(DataToExport(name='Analog Input',
                                          data=[DataFromPlugins(name='AI', data=data_tot,
                                                                dim='Data0D',
                                                                labels=[f'AI{channel_available[ind]} data '
                                                                        for ind, data in enumerate(data_tot)])]))


    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.disable_all_reporting()


if __name__ == '__main__':
    main(__file__)