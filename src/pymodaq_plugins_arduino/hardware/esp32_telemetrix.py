import asyncio
import numbers
import threading
from threading import Lock

from telemetrix_aio_esp32 import telemetrix_aio_esp32

lock = Lock()

# Maps GPIO pin numbers to ESP32 LEDC hardware channels.
# LEDC channels are required when configuring a pin as PWM output.
PIN_TO_CHANNEL = {
    17: 0,  # Fan    → LEDC channel 0
    18: 1,  # Heater → LEDC channel 1
}


class ArduinoWifi:
    """WiFi wrapper for the ESP32 board using the Telemetrix AIO protocol.

    This object exposes a subset of the Telemetrix API over a WiFi connection
    and mirrors the interface of the :class:`Arduino` (USB/telemetrix) class so
    that higher-level plugins can target either board with minimal changes.

    Attributes:
    -----------
    pin_values_output: dict
        Keeps track of the last value written to each output pin.
    analog_pin_values_input: dict
        Keeps track of the last value read from each analog input channel.
    """

    def __init__(self, ip_address: str):
        self.pin_values_output = {}
        self.analog_pin_values_input = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        future = asyncio.run_coroutine_threadsafe(
            self._init_board(ip_address), self._loop
        )
        future.result(timeout=10)

    async def _init_board(self, ip_address: str):
        self._board = telemetrix_aio_esp32.TelemetrixAioEsp32(
            transport_address=ip_address,
            autostart=False,
            loop=self._loop,
            restart_on_shutdown=False,
            shutdown_on_exception=False,
        )
        await self._board.start_aio()

    def _run(self, coro):
        """Submit a coroutine to the board event-loop and block until done."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=5)

    @staticmethod
    def round_value(value) -> int:
        """Clamp *value* to the valid PWM range [0, 255]."""
        return max(0, min(255, int(value)))

    def set_pin_mode_analog_output(self, pin: int):
        """Configure *pin* as a PWM output (LEDC) on the ESP32.

        The LEDC channel is resolved from :data:`PIN_TO_CHANNEL`; channel 0
        is used as fallback for unmapped pins.
        """
        channel = PIN_TO_CHANNEL.get(pin, 0)
        self._run(self._board.set_pin_mode_analog_output(pin_number=pin, channel=channel))

    def analog_write(self, pin: int, value: int):
        """Write a raw PWM duty cycle to *pin*.

        ESP32 Core v3.x uses ``ledcWrite(pin, value)`` where the GPIO number is
        passed directly as the channel identifier — hence ``channel=pin`` here.
        """
        self._run(self._board.analog_write(channel=pin, value=value))

    def analog_write_and_memorize(self, pin: int, value):
        """Write *value* to *pin* and record it in :attr:`pin_values_output`.

        The value is clamped to [0, 255] before being sent.
        Thread-safe.
        """
        lock.acquire()
        value = self.round_value(value)
        self.analog_write(pin, value)
        self.pin_values_output[pin] = value
        lock.release()

    def set_pins_output_to(self, value: int):
        """Write *value* to every pin that has been initialised as an output.

        Thread-safe.
        """
        lock.acquire()
        for pin in self.pin_values_output:
            self.analog_write(pin, int(value))
        lock.release()

    def get_output_pin_value(self, pin: int) -> numbers.Number:
        """Return the last value written to *pin*, or 0 if never written."""
        return self.pin_values_output.get(pin, 0)

    def shutdown(self):
        """Gracefully stop the Telemetrix session and the event-loop thread."""
        self._run(self._board.shutdown())
        self._loop.call_soon_threadsafe(self._loop.stop)
