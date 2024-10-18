import numbers
from threading import Lock

from pyvisa import ResourceManager
from telemetrix import telemetrix

lock = Lock()

VISA_rm = ResourceManager()
COM_PORTS = []
for name, rinfo in VISA_rm.list_resources_info().items():
    if rinfo.alias is not None:
        COM_PORTS.append(rinfo.alias)
    else:
        COM_PORTS.append(name)


class Arduino(telemetrix.Telemetrix):
    COM_PORTS = COM_PORTS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pin_values_output = {}
        self.analog_pin_values_input = {0: 0,
                                        1: 0,
                                        2: 0,
                                        3: 0,
                                        4: 0,
                                        5: 0}  # Initialized dictionary for 6 analog channels

    @staticmethod
    def round_value(value):
        return max(0, min(255, int(value)))

    def set_pins_output_to(self, value: int):
        lock.acquire()
        for pin in self.pin_values_output:
            self.analog_write(pin, int(value))
        lock.release()

    def analog_write_and_memorize(self, pin, value):
        lock.acquire()
        value = self.round_value(value)
        self.analog_write(pin, value)
        self.pin_values_output[pin] = value
        lock.release()

    def read_analog_pin(self, data):
        """
        Used as a callback function to read the value of the analog inputs.
        Data[0]: pin_type (not used here)
        Data[1]: pin_number: i.e. 0 is A0 etc.
        Data[2]: pin_value: an integer between 0 and 1023 (with an Arduino UNO)
        Data[3]: raw_time_stamp (not used here)
        :param data: a list in which are loaded the acquisition parameter analog input
        :return: a dictionary with the following structure {pin_number(int):pin_value(int)}
        With an arduino up to 6 analog input might be interrogated at the same time
        """
        self.analog_pin_values_input[data[1]] = data[2]  # data are integer from 0 to 1023 in case Arduino UNO

    def set_analog_input(self, pin):
        """
        Activate the analog pin, make an acquisition, write in the callback, stop the analog reporting
        :param pin: pin number 1 is A1 etc...
        :return: acquisition parameters in the declared callback
        The differential parameter:
            When comparing the previous value and the current value, if the
            difference exceeds the differential. This value needs to be equaled
            or exceeded for a callback report to be generated.
        """
        lock.acquire()
        self.set_pin_mode_analog_input(pin, differential=0, callback=self.read_analog_pin)
        self.set_analog_scan_interval(1)
        self.disable_analog_reporting(pin)
        lock.release()

    def get_output_pin_value(self, pin: int) -> numbers.Number:
        value = self.pin_values_output.get(pin, 0)
        return value

    def ini_i2c(self, port: int = 0):
        lock.acquire()
        self.set_pin_mode_i2c(port)
        lock.release()

    def writeto(self, addr, bytes_to_write: bytes):
        """ to use the interface proposed by the lcd_i2c package made for micropython originally"""
        lock.acquire()
        self.i2c_write(addr, [int.from_bytes(bytes_to_write, byteorder='big')])
        lock.release()

    def servo_move_degree(self, pin: int, value: float):
        """ Move a servo motor to the value in degree between 0 and 180 degree"""
        lock.acquire()
        self.servo_write(pin, int(value * 255 / 180))
        self.pin_values_output[pin] = value
        lock.release()


if __name__ == '__main__':
    import time
    tele = Arduino('COM6')
    tele.set_pin_mode_servo(5, 100, 3000)
    time.sleep(.2)

    tele.servo_write(5, 90)

    time.sleep(1)

    tele.servo_write(5, 00)

    tele.shutdown()