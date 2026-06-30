pymodaq_plugins_arduino
#######################

.. the following must be adapted to your developed package, links to pypi, github  description...

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_arduino.svg
   :target: https://pypi.org/project/pymodaq_plugins_arduino/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_arduino/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_arduino
   :alt: Publication Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_arduino/actions/workflows/Test.yml/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins_arduino/actions/workflows/Test.yml


This package regroups a list of instruments created around an Arduino or ESP32 board. Some
instruments use the Telemetrix library to use Python together with the Arduino board. Others use the
Telemetrix AIO ESP32 library to communicate with an ESP32 board over WiFi.

Authors
=======

* Sebastien J. Weber  (sebastien.weber@cemes.fr)
* Jérémie Margueritat
* Mohamed El Mokhtari (mohamed.elmokhtari26@gmail.com)
* Fabien Villedieu (fabien.villedieu.pro@gmail.com)

Instruments
===========

Below is the list of instruments included in this plugin

Actuators
+++++++++

* **LED**: control of a multicolor LED using three PWM digital outputs and the Telemetrix library.
  Allows the control of the three color channel independently

* **LEDwithLCD**: same as **LED** actuator but displaying the red, green, blue values on a standard 16x2 liquid crystal
  display

* **Servo**: control of a servo motor position (in degrees) on a digital pin using the Telemetrix
  library

* **Analog**: data acquisition from analog inputs

* **FanHeater**: control of a heater and a fan using two PWM outputs and the Telemetrix AIO ESP32
  library. Allows the control of the heater and fan independently over WiFi. The PWM duty cycle
  ranges from 0 to 255 (8-bit resolution)

Extensions
==========

* **ColorSynthesizer**: DashBoard extension using RBG LED actuators. Allows to quickly select a RGB value and apply those
  to the actuators

Viewers
=======

* **Voltage_ADS1115**: reads up to four single-ended analog voltages (AIN0–AIN3) from an ADS1115
  (16-bit) or ADS1015 (12-bit) I2C ADC. The PGA gain, data rate and number of active channels are
  configurable. Communication is performed over I2C by an ESP32 running the Telemetrix AIO WiFi
  firmware.

* **Temperature MAX31865**: reads temperature from a PT100 resistance temperature detector (RTD) wired to a
  MAX31865 amplifier/ADC board. Communication with the MAX31865 is performed over bit-banged SPI
  by an ESP32 running the Telemetrix AIO WiFi firmware.

Installation instructions
=========================

* PyMoDAQ version > 5.0.0

LED actuator
++++++++++++

The LED actuator uses the telemetrix library. The corresponding sketch should therefore be uploaded
on the arduino board. This allows to control peripheral on an Arduino board from python objects on the connected
computer. See https://mryslab.github.io/telemetrix/

LEDwithLCD actuator
+++++++++++++++++++

The **LEDwithLCD** actuator uses the telemetrix library. The corresponding sketch should therefore be uploaded
on the arduino board. It then uses the telemetrix I2C communication protocol to control a LCD equipped with a
I2C backpack. The functionalities used to drive the LCD are adapted from a micropython code
(https://github.com/brainelectronics/micropython-i2c-lcd) itself adapted from
https://github.com/fdebrabander/Arduino-LiquidCrystal-I2C-library

Servo actuator
++++++++++++++

The **Servo** actuator uses the telemetrix library. The corresponding sketch should therefore be
uploaded on the arduino board. This allows to drive a servo motor connected to a digital pin of the
Arduino board, the position being commanded in degrees. See https://mryslab.github.io/telemetrix/

Analog 0D viewer
++++++++++++++++

The **Analog** 0D viewer uses the telemetrix library. The corresponding sketch should therefore be uploaded
on the arduino board. This allows to acquire data from the analog inputs on an Arduino board from python objects on
the connected computer. See https://mryslab.github.io/telemetrix/

FanHeater actuator
++++++++++++++++++

The **FanHeater** actuator uses the telemetrix-aio-esp32 library. The corresponding firmware should
therefore be uploaded on the ESP32 board. This allows to control a heater and a fan connected to
the ESP32 over WiFi from python objects on the connected computer.
See https://mryslab.github.io/telemetrix-esp32/

Voltage_ADS1115 0D viewer
+++++++++++++++++++++++++

The **Voltage_ADS1115** 0D viewer uses the telemetrix-aio-esp32 library. The corresponding firmware
should therefore be uploaded on the ESP32 board. This allows to acquire analog voltages from an
ADS1115/ADS1015 I2C ADC connected to the ESP32 over WiFi.
See https://mryslab.github.io/telemetrix-esp32/

Temperature MAX31865 0D viewer
+++++++++++++++

The **Temperature MAX31865** 0D viewer uses the telemetrix-aio-esp32 library. The corresponding firmware should
therefore be uploaded on the ESP32 board. This allows to acquire temperature data from a PT100
sensor wired to a MAX31865 board connected to the ESP32 over WiFi.

Here are `detailed installation instructions <https://pymodaq.cnrs.fr/en/latest/lab_story_folder/arduino_ubuntu.html#>`_.

Wiki
====

Additional documentation for this fork is available on the dedicated Wiki:
https://wiki-plugins-dap-pymodaq.github.io/


