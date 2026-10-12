from typing import Optional

import numpy as np
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.hardware.sensors.max31865.spi_max31865 import MAX31865
from pymodaq_plugins_arduino.utils import Config

config = Config()


class DAQ_0DViewer_Temperature_MAX31865(DAQ_Viewer_base):
    """Instrument plugin class for a 0D viewer.

    This object inherits all functionalities to communicate with PyMoDAQ's DAQ_Viewer module through
    inheritance via DAQ_Viewer_base.  It makes a bridge between the DAQ_Viewer module and the Python
    wrapper of a particular instrument.

    This plugin reads temperature from a PT100 resistance temperature detector (RTD) wired to a
    MAX31865 amplifier/ADC board.  Communication with the MAX31865 is performed over bit-banged SPI
    by an ESP32 running the Telemetrix AIO WiFi firmware.

    The four SPI pin numbers (SCK, MISO, MOSI, CS) are configurable from the PyMoDAQ parameter tree
    or from *config_template.toml*.

    Attributes:
    -----------
    controller: object
        The particular object that allows communication with the hardware, in general a Python
        wrapper around the hardware library.
    max31865: MAX31865
        The driver object for the MAX31865 chip.
    """

    _controller_units = '°C'

    params = comon_parameters + [
        {'title': 'Connection', 'name': 'connection', 'type': 'group', 'children': [
            {'title': 'IP Address:', 'name': 'ip_address', 'type': 'str',
             'value': config('esp32', 'ip_address')},
        ]},
        {'title': 'SPI Pins (GPIO)', 'name': 'spi_pins', 'type': 'group', 'children': [
            {'title': 'SCK pin:',  'name': 'sck_pin',  'type': 'int',
             'value': config('max31865', 'sck_pin'),
             'tip': 'Nano ESP32 legacy: D13 = GPIO48'},
            {'title': 'MISO pin:', 'name': 'miso_pin', 'type': 'int',
             'value': config('max31865', 'miso_pin'),
             'tip': 'Nano ESP32 legacy: D12 = GPIO47'},
            {'title': 'MOSI pin:', 'name': 'mosi_pin', 'type': 'int',
             'value': config('max31865', 'mosi_pin'),
             'tip': 'Nano ESP32 legacy: D11 = GPIO38'},
            {'title': 'CS pin:',   'name': 'cs_pin',   'type': 'int',
             'value': config('max31865', 'cs_pin'),
             'tip': 'Nano ESP32 legacy: D10 = GPIO21'},
        ]},
    ]

    def ini_attributes(self):
        self.controller: Optional[ArduinoWifi] = None
        self.max31865: Optional[MAX31865] = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        pass

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by
            controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:
            self.controller = ArduinoWifi(
                ip_address=self.settings['connection', 'ip_address']
            )
        else:
            self.controller = controller

        self.max31865 = MAX31865(
            controller=self.controller,
            sck_pin=self.settings['spi_pins', 'sck_pin'],
            miso_pin=self.settings['spi_pins', 'miso_pin'],
            mosi_pin=self.settings['spi_pins', 'mosi_pin'],
            cs_pin=self.settings['spi_pins', 'cs_pin'],
        )
        self.max31865.ini_max31865()

        info = "Temperature MAX31865 ready"
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master and self.controller is not None:
            self.controller.shutdown()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging
            should be set to True in class preamble and you should code this implementation)
        kwargs: dict
            others optional arguments
        """
        temperature = self.max31865.get_temperature()
        self.dte_signal.emit(DataToExport(
            name='Temperature MAX31865',
            data=[DataFromPlugins(
                name='Temperature',
                data=[np.array([temperature])],
                dim='Data0D',
                labels=['Temperature (°C)'],
            )]
        ))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        pass


if __name__ == '__main__':
    main(__file__)
