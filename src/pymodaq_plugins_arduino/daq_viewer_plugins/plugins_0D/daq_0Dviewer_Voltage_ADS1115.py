from typing import Optional

import numpy as np
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.hardware.sensors.ads1115.i2c_ads1115 import ADS1115, GAIN_CONFIG, DATA_RATE_CONFIG
from pymodaq_plugins_arduino.utils import Config

config = Config()


class DAQ_0DViewer_Voltage_ADS1115(DAQ_Viewer_base):
    """Instrument plugin class for a 0D viewer.

    This object inherits all functionalities to communicate with PyMoDAQ's DAQ_Viewer module through
    inheritance via DAQ_Viewer_base.  It makes a bridge between the DAQ_Viewer module and the Python
    wrapper of a particular instrument.

    This plugin reads analog voltages from an ADS1115 (16-bit) or ADS1015 (12-bit) I2C ADC.
    Communication is performed over I2C by an ESP32 running the Telemetrix AIO WiFi firmware.

    Up to 4 single-ended channels (AIN0–AIN3) can be acquired simultaneously.  The number of
    active channels, the PGA gain, and the data rate are configurable from the parameter tree.

    Attributes:
    -----------
    controller: ArduinoWifi
        Connection to the ESP32 board.
    ads: ADS1115
        Low-level driver for the ADS1115/ADS1015 chip.
    """

    _controller_units = 'V'

    params = comon_parameters + [
        {'title': 'Connection', 'name': 'connection', 'type': 'group', 'children': [
            {'title': 'IP Address:', 'name': 'ip_address', 'type': 'str',
             'value': config('esp32', 'ip_address')},
        ]},
        {'title': 'I2C Settings', 'name': 'i2c', 'type': 'group', 'children': [
            {'title': 'I2C Address (hex):', 'name': 'i2c_address', 'type': 'int',
             'value': config('ads1115', 'i2c_address'),
             'tip': '0x48=ADDR→GND  0x49=ADDR→VDD  0x4A=ADDR→SDA  0x4B=ADDR→SCL'},
            {'title': 'SDA pin:', 'name': 'sda_pin', 'type': 'int',
             'value': config('ads1115', 'sda_pin'),
             'tip': 'Nano ESP32 : A4 = GPIO11 (SDA par défaut)'},
            {'title': 'SCL pin:', 'name': 'scl_pin', 'type': 'int',
             'value': config('ads1115', 'scl_pin'),
             'tip': 'Nano ESP32 : A5 = GPIO12 (SCL par défaut)'},
        ]},
        {'title': 'ADC Settings', 'name': 'adc', 'type': 'group', 'children': [
            {'title': 'Chip type:', 'name': 'chip_type', 'type': 'list',
             'limits': ['ADS1115 (16-bit)', 'ADS1015 (12-bit)'],
             'value': 'ADS1115 (16-bit)'},
            {'title': 'Gain (PGA):', 'name': 'gain', 'type': 'list',
             'limits': list(GAIN_CONFIG.keys()),
             'value': config('ads1115', 'gain'),
             'tip': 'Gain × → full-scale range: 2/3×→±6.144V  1×→±4.096V  2×→±2.048V  4×→±1.024V  8×→±0.512V  16×→±0.256V'},
            {'title': 'Data rate (SPS):', 'name': 'data_rate', 'type': 'list',
             'limits': list(DATA_RATE_CONFIG.keys()),
             'value': 128},
            {'title': 'Active channels:', 'name': 'num_channels', 'type': 'int',
             'value': 1, 'min': 1, 'max': 4,
             'tip': 'Number of single-ended channels to read (AIN0 … AIN(n-1))'},
        ]},
    ]

    def ini_attributes(self):
        self.controller: Optional[ArduinoWifi] = None
        self.ads: Optional[ADS1115] = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings.

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() in ('gain', 'data_rate', 'chip_type'):
            if self.ads is not None:
                self.ads.gain       = self.settings['adc', 'gain']
                self.ads.data_rate  = self.settings['adc', 'data_rate']
                self.ads.is_ads1015 = self.settings['adc', 'chip_type'] == 'ADS1015 (12-bit)'

    def ini_detector(self, controller=None):
        """Detector communication initialization.

        Parameters
        ----------
        controller: object
            Custom object of a PyMoDAQ plugin (Slave case). None if this is the Master.

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True.
        """

        if self.is_master:
            self.controller = ArduinoWifi(
                ip_address=self.settings['connection', 'ip_address']
            )
        else:
            self.controller = controller

        self.ads = ADS1115(
            controller=self.controller,
            i2c_address=self.settings['i2c', 'i2c_address'],
            sda_pin=self.settings['i2c', 'sda_pin'],
            scl_pin=self.settings['i2c', 'scl_pin'],
            gain=self.settings['adc', 'gain'],
            data_rate=self.settings['adc', 'data_rate'],
            is_ads1015=self.settings['adc', 'chip_type'] == 'ADS1015 (12-bit)',
        )
        self.ads.ini_ads1115()

        info = "Voltage ADS1115 ready"
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol."""
        if self.is_master and self.controller is not None:
            self.controller.shutdown()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector.

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging iterations.
        kwargs: dict
            Other optional arguments.
        """
        num_channels = self.settings['adc', 'num_channels']

        voltages = []
        labels   = []
        for ch in range(num_channels):
            voltages.append(np.array([self.ads.get_voltage(ch)]))
            labels.append(f'AIN{ch} (V)')

        self.dte_signal.emit(DataToExport(
            name='Voltage ADS1115',
            data=[DataFromPlugins(
                name='Voltage',
                data=voltages,
                dim='Data0D',
                labels=labels,
            )]
        ))

    def stop(self):
        """Stop the current grab hardware wise if necessary."""
        pass


if __name__ == '__main__':
    main(__file__)
