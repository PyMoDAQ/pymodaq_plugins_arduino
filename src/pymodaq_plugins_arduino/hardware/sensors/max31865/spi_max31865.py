import asyncio

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.utils import Config

config = Config()

SPI_INIT = 22

# ── MAX31865 register map ────────────────────────────────────────────────────
MAX31865_CONFIG_REG      = 0x00   # Configuration register (write address = reg | 0x80)
MAX31865_CONFIG_BIAS     = 0x80   # Bias voltage ON
MAX31865_CONFIG_MODEAUTO = 0x40   # Auto (continuous) conversion mode
MAX31865_RTDMSB_REG      = 0x01   # RTD resistance data MSB (read-only)

# ── PT100 Callendar-Van Dusen coefficients ───────────────────────────────────
RTD_NOMINAL   = 100.0    # PT100 nominal resistance at 0 °C (Ω)
RTD_REFERENCE = 430.0    # Default reference resistor (Ω) — Adafruit boards use
                         # 430 Ω, but clones ship with 350/390/400 Ω: check the
                         # SMD resistor marked Rref next to the chip.
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
                 miso_pin: int = None, mosi_pin: int = None,
                 ref_resistor: float = None):
        # Borrow the board handle and the synchronous _run helper from the controller
        self._board = controller._board
        self._run   = controller._run

        self.cs_pin   = cs_pin   or config('max31865', 'cs_pin')
        self.sck_pin  = sck_pin  or config('max31865', 'sck_pin')
        self.miso_pin = miso_pin or config('max31865', 'miso_pin')
        self.mosi_pin = mosi_pin or config('max31865', 'mosi_pin')
        self.ref_resistor = ref_resistor or RTD_REFERENCE

    def ini_max31865(self):
        """Initialise the SPI bus and put the MAX31865 in auto-conversion mode.

        Sequence:
        1. Send SPI_INIT manually with all four pin numbers.
           (set_pin_mode_spi([cs]) only forwards the CS pin; the firmware's
           init_spi() also needs SCK, MISO and MOSI.)
        2. Force the internal Telemetrix flags that gate spi_cs_control().
           (Bypassing set_pin_mode_spi leaves spi_enabled=False.)
        3. Set the SPI format: the MAX31865 requires SPI mode 1 or 3
           (CPHA=1); the firmware default is mode 0, which the chip ignores.
        4. Write the configuration byte: bias voltage ON + auto conversion.

        Requires firmware >= 3.1.1 (read address sent as-is + SPI format
        actually applied through SPI.beginTransaction()).
        """
        self._run(self._manual_spi_init())
        # Telemetrix gates spi_cs_control() behind these two flags; set them
        # manually because we bypassed the normal set_pin_mode_spi path.
        self._board.spi_enabled = True
        if self.cs_pin not in self._board.cs_pins_enabled:
            self._board.cs_pins_enabled.append(self.cs_pin)

        # 1 MHz (divisor 16 of the Arduino 16 MHz convention), MSB first,
        # SPI mode 1 (AVR constant 0x04) as required by the MAX31865.
        self._run(self._board.spi_set_format(16, 1, 0x04))

        config_byte = MAX31865_CONFIG_BIAS | MAX31865_CONFIG_MODEAUTO
        self._run(self._board.spi_cs_control(self.cs_pin, 0))
        self._run(self._board.spi_write_blocking([MAX31865_CONFIG_REG | 0x80, config_byte]))
        self._run(self._board.spi_cs_control(self.cs_pin, 1))

    async def _manual_spi_init(self):
        """Send SPI_INIT (cmd 22) with all four pin numbers explicitly.

        Payload expected by firmware init_spi():
            [sck_pin, miso_pin, mosi_pin, num_cs=1, cs_pin]
        """
        await self._board._send_command([SPI_INIT,
                                         self.sck_pin, self.miso_pin, self.mosi_pin,
                                         1, self.cs_pin])

    def read_rtd_resistance(self) -> float:
        """Read the raw RTD register and return the equivalent resistance in Ω.

        The MAX31865 stores the 15-bit ADC result in registers 0x01 (MSB) and
        0x02 (LSB).  Bit 0 of the LSB is the fault flag and is discarded by
        shifting right one position before computing the resistance.

        Note: requires the firmware fix — read_blocking_spi must NOT OR the
        register address with 0x80 (MAX31865 convention: bit7=0 = read).
        """
        data = []

        async def read():
            # asyncio.Event must be created inside the running event-loop thread
            event = asyncio.Event()

            async def spi_callback(report):
                # report layout from firmware: [len, SPI_REPORT, reg, num_bytes, byte0, byte1, ...]
                # report[3:] = [byte0, byte1, ...]
                data.extend(report[3:])
                event.set()

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
        resistance = (rtd_raw / 32768.0) * self.ref_resistor
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
