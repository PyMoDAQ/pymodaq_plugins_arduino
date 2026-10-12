import asyncio
import time

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.utils import Config

config = Config()

I2C_BEGIN = 9

# ADS1115/ADS1015 register addresses
ADS_REG_CONVERSION = 0x00
ADS_REG_CONFIG     = 0x01

# MUX bits for single-ended channels (bits 14:12 of config register)
_MUX_SINGLE = {
    0: 0x4000,  # AIN0 vs GND
    1: 0x5000,  # AIN1 vs GND
    2: 0x6000,  # AIN2 vs GND
    3: 0x7000,  # AIN3 vs GND
}

# PGA (Gain) settings: gain_label -> (config_bits, full-scale range in V)
GAIN_CONFIG = {
    '2/3': (0x0000, 6.144),
    '1':   (0x0200, 4.096),
    '2':   (0x0400, 2.048),
    '4':   (0x0600, 1.024),
    '8':   (0x0800, 0.512),
    '16':  (0x0A00, 0.256),
}

# Data rate bits (bits 7:5 of config register)
DATA_RATE_CONFIG = {
    8:   0x0000,
    16:  0x0020,
    32:  0x0040,
    64:  0x0060,
    128: 0x0080,
    250: 0x00A0,
    475: 0x00C0,
    860: 0x00E0,
}


class ADS1115:
    """Software driver for the ADS1115 / ADS1015 I2C ADC.

    Communicates with the chip over I2C via the Telemetrix AIO firmware
    running on the ESP32.  Pins and address are configurable at construction
    time or read from *config_template.toml*.

    Attributes:
    -----------
    i2c_address: int
        7-bit I2C address of the chip (0x48–0x4B depending on ADDR pin).
    sda_pin, scl_pin: int
        GPIO numbers for the I2C bus.
    gain: str
        PGA gain label (one of '2/3', '1', '2', '4', '8', '16').
    data_rate: int
        Samples per second (8, 16, 32, 64, 128, 250, 475, 860).
    is_ads1015: bool
        True for ADS1015 (12-bit); False for ADS1115 (16-bit, default).
    """

    def __init__(self, controller: ArduinoWifi,
                 i2c_address: int = None,
                 sda_pin: int = None,
                 scl_pin: int = None,
                 gain: str = '1',
                 data_rate: int = 128,
                 is_ads1015: bool = False):
        self._board = controller._board
        self._run   = controller._run

        self.i2c_address = i2c_address if i2c_address is not None else config('ads1115', 'i2c_address')
        self.sda_pin     = sda_pin     if sda_pin     is not None else config('ads1115', 'sda_pin')
        self.scl_pin     = scl_pin     if scl_pin     is not None else config('ads1115', 'scl_pin')
        self.gain        = gain
        self.data_rate   = data_rate
        self.is_ads1015  = is_ads1015

    def ini_ads1115(self):
        """Initialise the I2C bus on the ESP32.

        set_pin_mode_i2c() in telemetrix_aio_esp32 2.0.0 takes no pin
        arguments, so the I2C_BEGIN command is sent manually with the
        SDA/SCL pins as payload.  Firmware >= 3.1.2 applies them through
        Wire.begin(sda, scl); older firmwares ignore the payload and use
        the board defaults (A4 = GPIO11 / A5 = GPIO12 on the Nano ESP32,
        which match the config defaults).
        """
        async def _begin():
            await self._board._send_command(
                [I2C_BEGIN, self.sda_pin, self.scl_pin])

        self._run(_begin())
        # The lib gates i2c_read/i2c_write behind this flag; set it manually
        # because we bypassed set_pin_mode_i2c().
        self._board.i2c_active = True

    def read_channel(self, channel: int) -> float:
        """Trigger a single-ended conversion on *channel* and return the voltage in V.

        Parameters
        ----------
        channel: int
            Analog input channel, 0–3 (AIN0–AIN3 vs GND).

        Returns
        -------
        float
            Measured voltage in volts.
        """
        if channel not in _MUX_SINGLE:
            raise ValueError(f"Channel must be 0–3, got {channel}")

        gain_bits, fsr = GAIN_CONFIG[self.gain]
        dr_bits = DATA_RATE_CONFIG.get(self.data_rate, 0x0080)

        # Build 16-bit config register:
        #   OS=1 (start single-shot), MUX, PGA, MODE=1 (single-shot),
        #   DR, COMP_MODE/POL/LAT=0, COMP_QUE=11 (disabled)
        config_reg = (
            0x8000               |
            _MUX_SINGLE[channel] |
            gain_bits            |
            0x0100               |  # single-shot mode
            dr_bits              |
            0x0003                  # disable comparator
        )

        msb = (config_reg >> 8) & 0xFF
        lsb = config_reg & 0xFF

        # Write config register to start conversion
        self._run(self._board.i2c_write(
            self.i2c_address,
            [ADS_REG_CONFIG, msb, lsb],
        ))

        # Allow time for conversion: 1/data_rate + margin
        time.sleep(1.0 / self.data_rate + 0.002)

        # Read 2 bytes from conversion register
        data = []

        async def _read():
            event = asyncio.Event()

            async def _callback(report):
                # Firmware sends: [len, I2C_READ_REPORT, num_bytes, address, register, byte0, ...]
                # Python lib strips len → report = [I2C_READ_REPORT, num_bytes, address, register, byte0, ...]
                # Data bytes start at index 4.
                data.extend(report[4:4 + report[1]])
                event.set()

            await self._board.i2c_read(
                self.i2c_address,
                ADS_REG_CONVERSION,
                2,
                _callback,
            )
            await asyncio.wait_for(event.wait(), timeout=5)

        self._run(_read())

        raw = (data[0] << 8) | data[1]

        # ADS1015 result occupies the upper 12 bits → shift right by 4
        if self.is_ads1015:
            raw >>= 4
            full_scale = 2048.0
        else:
            full_scale = 32768.0

        # Convert unsigned raw to signed (two's complement)
        half = int(full_scale)
        if raw >= half:
            raw -= 2 * half

        return (raw / full_scale) * fsr

    def get_voltage(self, channel: int) -> float:
        """Return the voltage (V) measured on *channel* (0–3)."""
        return self.read_channel(channel)
