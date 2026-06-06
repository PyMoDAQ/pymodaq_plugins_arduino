import asyncio

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.utils import Config

config = Config()

# ── MAX31865 register map ────────────────────────────────────────────────────
MAX31865_CONFIG_REG      = 0x00   # Configuration register (write address = reg | 0x80)
MAX31865_CONFIG_BIAS     = 0x80   # Bias voltage ON
MAX31865_CONFIG_MODEAUTO = 0x40   # Auto (continuous) conversion mode
MAX31865_RTDMSB_REG      = 0x01   # RTD resistance data MSB (read-only)

# ── PT100 Callendar-Van Dusen coefficients ───────────────────────────────────
RTD_NOMINAL   = 100.0    # PT100 nominal resistance at 0 °C (Ω)
RTD_REFERENCE = 430.0    # Reference resistor mounted on the MAX31865 board (Ω)
RTD_A =  3.9083e-3       # CVD coefficient A
RTD_B = -5.775e-7        # CVD coefficient B


class MAX31865:
    """Software driver for the MAX31865 RTD-to-digital converter.

    Communicates with the chip over bit-banged SPI via the Telemetrix AIO
    firmware running on the ESP32.  The four SPI pins can be passed at
    construction time or read from *config_template.toml*.

    Attributes:
    -----------
    cs_pin, sck_pin, miso_pin, mosi_pin: int
        GPIO numbers of the four SPI lines.
    """

    def __init__(self, controller: ArduinoWifi,
                 cs_pin: int = None, sck_pin: int = None,
                 miso_pin: int = None, mosi_pin: int = None):
        # Borrow the board handle and the synchronous _run helper from the controller
        self._board = controller._board
        self._run   = controller._run

        self.cs_pin   = cs_pin   or config('max31865', 'cs_pin')
        self.sck_pin  = sck_pin  or config('max31865', 'sck_pin')
        self.miso_pin = miso_pin or config('max31865', 'miso_pin')
        self.mosi_pin = mosi_pin or config('max31865', 'mosi_pin')

    def ini_max31865(self):
        """Initialise the SPI bus and put the MAX31865 in auto-conversion mode.

        Sequence:
        1. Register the CS pin with Telemetrix (``set_pin_mode_spi``).
        2. Write the configuration byte that enables the bias voltage and
           selects continuous conversion.
        """
        self._run(self._board.set_pin_mode_spi([self.cs_pin]))

        config_byte = MAX31865_CONFIG_BIAS | MAX31865_CONFIG_MODEAUTO
        self._run(self._board.spi_cs_control(self.cs_pin, 0))
        self._run(self._board.spi_write_blocking([MAX31865_CONFIG_REG | 0x80, config_byte]))
        self._run(self._board.spi_cs_control(self.cs_pin, 1))

    def read_rtd_resistance(self) -> float:
        """Read the raw RTD register and return the equivalent resistance in Ω.

        The MAX31865 stores the 15-bit ADC result in registers 0x01 (MSB) and
        0x02 (LSB).  Bit 0 of the LSB is the fault flag and is discarded by
        shifting right one position before computing the resistance.
        """
        data  = []
        event = asyncio.Event()

        async def spi_callback(report):
            data.extend(report[3:])
            event.set()

        async def read():
            await self._board.spi_cs_control(self.cs_pin, 0)
            await self._board.spi_read_blocking(
                MAX31865_RTDMSB_REG,
                2,
                call_back=spi_callback,
            )
            await asyncio.wait_for(event.wait(), timeout=5)
            await self._board.spi_cs_control(self.cs_pin, 1)

        self._run(read())

        rtd_raw    = ((data[0] << 8) | data[1]) >> 1   # discard fault bit (LSB)
        resistance = (rtd_raw / 32768.0) * RTD_REFERENCE
        return resistance

    def resistance_to_temperature(self, resistance: float) -> float:
        """Convert a resistance (Ω) to temperature (°C) via the Callendar-Van Dusen equation.

        This approximation is valid for T > 0 °C.
        """
        z1 = -RTD_A
        z2 =  RTD_A ** 2 - (4 * RTD_B)
        z3 = (4 * RTD_B) / RTD_NOMINAL
        z4 =  2 * RTD_B
        temp = (((z2 + z3 * resistance) ** 0.5) + z1) / z4
        return temp

    def get_temperature(self) -> float:
        """Return the current probe temperature in °C."""
        resistance = self.read_rtd_resistance()
        return self.resistance_to_temperature(resistance)
