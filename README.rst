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


This package regroups a list of instrument created around an arduino board. Some instruments use the
Telemetrix library to use python together with the arduino board.


Authors
=======

* Sebastien J. Weber  (sebastien.weber@cemes.fr)
* Jérémie Margueritat


Instruments
===========

Below is the list of instruments included in this plugin

Actuators
+++++++++

* **LED**: control of a multicolor LED using three PWM digital outputs and the Telemetrix library.
  Allows the control of the three color channel independently
* **LEDwithLCD**: same as **LED** actuator but displaying the red, green, blue values on a standard 16x2 liquid crystal
  display
* **Analog**: data acquisition from analog inputs



Extensions
==========

* **ColorSynthesizer**: DashBoard extension using RBG LED actuators. Allows to quicly select a RGB value and apply those
  to the actuators


Installation instructions
=========================

* PyMoDAQ version > 4.1.0


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

Analog 0D viewer
++++++++++++++++

The **Analog** 0D viewer uses the telemetrix library. The corresponding sketch should therefore be uploaded
on the arduino board. This allows to acquire data from the analog inputs on an Arduino board from python objects on
the connected computer. See https://mryslab.github.io/telemetrix/

